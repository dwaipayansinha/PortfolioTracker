from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings
import os
import json
import requests
import diskcache
from datetime import datetime
import time
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

warnings.filterwarnings("ignore")

# Create a robust session for yfinance to prevent rate limiting and handle retries
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND * 5)),  # Max 2 requests per 5 seconds
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance_cache.sqlite", expire_after=3600),
)

app = FastAPI()

# Setup persistent disk cache for final processed data
cache = diskcache.Cache("api_cache")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIOS = {
    "TD (One-Click 2026)": {
        "TD Conservative ETF Portfolio": "TCON.TO",
        "TD Balanced ETF Portfolio": "TBAL.TO",
        "TD Growth ETF Portfolio": "TGRO.TO",
        "TD All-Equity ETF Portfolio": "TEQT.TO",
    },
    "BMO (Income & Growth)": {
        "BMO Conservative Portfolio": "ZCON.TO",
        "BMO Balanced Portfolio": "ZBAL.TO",
        "BMO Growth Portfolio": "ZGRO.TO",
        "BMO All-Equity Portfolio": "ZEQT.TO",
        "BMO All-Equity Cash Flow (ZEQT.T)": "ZEQT.TO",
    },
    "CIBC (New 2025/2026)": {
        "CIBC Balanced ETF Portfolio": "CBLN.TO",
        "CIBC Balanced Growth ETF Portfolio": "CGRW.TO",
        "CIBC All-Equity (Avantis Partnership)": "CAGE.TO",
    },
    "iShares (RBC Partner)": {
        "iShares Core Conservative (XCON)": "XCON.TO",
        "iShares Core Balanced (XBAL)": "XBAL.TO",
        "iShares Core Growth (XGRO)": "XGRO.TO",
        "iShares Core All-Equity (XEQT)": "XEQT.TO",
    },
    "Vanguard (Global Standard)": {
        "Vanguard Conservative (VCNS)": "VCNS.TO",
        "Vanguard Balanced (VBAL)": "VBAL.TO",
        "Vanguard Growth (VGRO)": "VGRO.TO",
        "Vanguard All-Equity (VEQT)": "VEQT.TO",
        "Scotia Balanced Exposure (BNS)": "BNS.TO",
    }
}

RENAME_FILE = "renamed_tickers.json"

def get_renamed_ticker(old_ticker):
    if os.path.exists(RENAME_FILE):
        with open(RENAME_FILE, 'r') as f:
            try:
                renames = json.load(f)
                return renames.get(old_ticker, old_ticker)
            except:
                return old_ticker
    return old_ticker

def save_rename(old_ticker, new_ticker):
    renames = {}
    if os.path.exists(RENAME_FILE):
        with open(RENAME_FILE, 'r') as f:
            try: renames = json.load(f)
            except: pass
    renames[old_ticker] = new_ticker
    with open(RENAME_FILE, 'w') as f:
        json.dump(renames, f)

def find_portfolio_name(ticker):
    for bank, funds in PORTFOLIOS.items():
        for name, t in funds.items():
            if t == ticker: return name
    return None

def robust_download(ticker, period, interval, attempts=3):
    """Downloads data with manual retries and fallback logic."""
    for i in range(attempts):
        try:
            data = yf.download(ticker, period=period, interval=interval, session=session, progress=False)
            if not data.empty:
                return data
            # If intraday (1d/1w) failed, try a larger interval
            if interval in ["5m", "1h"]:
                data = yf.download(ticker, period=period, interval="1d", session=session, progress=False)
                if not data.empty: return data
        except Exception as e:
            print(f"Attempt {i+1} failed for {ticker}: {e}")
            if i < attempts - 1:
                time.sleep(1) # Wait before retry
    return pd.DataFrame()

def resolve_ticker(ticker):
    current_ticker = get_renamed_ticker(ticker)
    data = robust_download(current_ticker, "1d", "1d", attempts=1)
    if not data.empty: return current_ticker
        
    name = find_portfolio_name(ticker)
    if name:
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={name}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = session.get(url, headers=headers, timeout=5)
            search_data = res.json()
            if search_data.get('quotes'):
                for quote in search_data['quotes']:
                    if quote.get('symbol') and quote.get('symbol') != current_ticker:
                         new_ticker = quote['symbol']
                         verify = yf.download(new_ticker, period="1d", session=session, progress=False)
                         if not verify.empty:
                             save_rename(ticker, new_ticker)
                             return new_ticker
        except Exception as e:
            print(f"Search failed for {name}: {e}")
    return current_ticker

@app.get("/api/portfolios")
def get_portfolios():
    return PORTFOLIOS

@app.get("/api/historical/{ticker}")
def get_historical(ticker: str, range: str = "1w"):
    resolved_ticker = resolve_ticker(ticker)
    cache_key = f"hist_{resolved_ticker}_{range}"
    
    range_to_period = {
        "1d": "1d", "1w": "5d", "1m": "1mo", "6m": "6mo",
        "1y": "1y", "5y": "5y", "10y": "10y", "max": "max"
    }
    interval_map = {
        "1d": "5m", "1w": "1h", "1m": "1d", "6m": "1d",
        "1y": "1d", "5y": "1wk", "10y": "1mo", "max": "1mo"
    }
    
    yf_period = range_to_period.get(range, "1y")
    interval = interval_map.get(range, "1d")
    
    try:
        data = robust_download(resolved_ticker, yf_period, interval)
        
        # Final fallback to max if still empty
        if data.empty and yf_period != "max":
            data = robust_download(resolved_ticker, "max", "1d")
            
        if data.empty:
             cached_val = cache.get(cache_key)
             if cached_val: return cached_val
             raise HTTPException(status_code=404, detail=f"No data found for ticker {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        data.reset_index(inplace=True)
        date_col = data.columns[0]
        data['time'] = data[date_col].astype(str)
        result = data[['time', 'Close']].rename(columns={'Close': 'value'}).dropna().to_dict(orient='records')
        
        cache.set(cache_key, result, expire=3600) 
        return result
    except Exception as e:
        cached_val = cache.get(cache_key)
        if cached_val: return cached_val
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{ticker}")
def get_analysis(ticker: str):
    resolved_ticker = resolve_ticker(ticker)
    cache_key = f"analysis_{resolved_ticker}"
    
    try:
        data = robust_download(resolved_ticker, "2y", "1d")
        if data.empty:
            data = robust_download(resolved_ticker, "max", "1d")
            
        if data.empty:
             cached_val = cache.get(cache_key)
             if cached_val: return cached_val
             raise HTTPException(status_code=404, detail=f"No data found for analysis on {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        closes = data['Close'].dropna()
        if len(closes) < 10: # Minimum data for basic analysis
             return {"recommendation": "Diversify", "confidence": 50, "reasons": ["Insufficient history for AI model"]}
             
        sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else closes.mean()
        sma_200 = closes.rolling(window=200).mean().iloc[-1] if len(closes) >= 200 else sma_50
        current_price = closes.iloc[-1]
        
        returns = closes.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        annual_return = returns.mean() * 252
        sharpe = annual_return / volatility if volatility > 0.0001 else 0
        
        lookback = min(100, len(closes))
        y = closes.values[-lookback:]
        X = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.array([[len(y) + 30]])
        forecast_price = model.predict(future_X)[0]
        
        score = 0
        reasons = []
        if current_price > sma_50: score += 1; reasons.append("Price is above 50-day SMA (Bullish).")
        else: score -= 1; reasons.append("Price is below 50-day SMA (Bearish).")
        if sma_50 > sma_200: score += 1; reasons.append("Golden Cross active (50SMA > 200SMA).")
        else: score -= 1; reasons.append("Death Cross active (50SMA < 200SMA).")
        if sharpe > 0.4: score += 1; reasons.append(f"Strong risk-adjusted returns (Sharpe: {sharpe:.2f}).")
        elif sharpe < 0: score -= 1; reasons.append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f}).")
        if forecast_price > current_price * 1.015: score += 2; reasons.append(f"ML Model forecasts >1.5% growth in 30 days.")
        elif forecast_price < current_price: score -= 2; reasons.append(f"ML Model forecasts price drop.")
            
        rec = "Invest" if score >= 2 else "Remove" if score <= -2 else "Diversify"
        conf = min(100, 50 + abs(score) * 10) if rec != "Diversify" else 60
            
        result = {
            "recommendation": rec, "confidence": conf, "reasons": reasons,
            "metrics": {
                "currentPrice": round(float(current_price), 2),
                "sma50": round(float(sma_50), 2),
                "sma200": round(float(sma_200), 2),
                "sharpeRatio": round(float(sharpe), 2),
                "forecast30d": round(float(forecast_price), 2)
            }
        }
        cache.set(cache_key, result, expire=3600)
        return result
    except Exception as e:
        cached_val = cache.get(cache_key)
        if cached_val: return cached_val
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
