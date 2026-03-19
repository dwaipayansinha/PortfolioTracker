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
from datetime import datetime, timedelta
import time
import re

warnings.filterwarnings("ignore")

app = FastAPI()

# Setup persistent disk cache
cache = diskcache.Cache("api_cache")

# API Keys
FMP_API_KEY = "gjKkPLDKVAvvtXON3D9Yfvij9dZI9Ibo"
TWELVE_DATA_API_KEY = "e60c246821d8495c8553022f50b404d8"

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
        "iShares Core Conservative (XCNS)": "XCNS.TO",
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

# --- Fallback Logic & Data Fetchers ---

TIMEFRAME_ORDER = ["max", "10y", "5y", "1y", "6m", "1m", "5d", "1d"]

PERIOD_TO_DAYS = {
    "1d": 1, "5d": 7, "1m": 31, "6m": 183, "1y": 366, "5y": 1826, "10y": 3653, "max": 7300
}

def get_next_shorter_period(current_period):
    try:
        idx = TIMEFRAME_ORDER.index(current_period)
        if idx + 1 < len(TIMEFRAME_ORDER):
            return TIMEFRAME_ORDER[idx + 1]
    except ValueError:
        pass
    return None

def fetch_fmp_data(ticker, period_days):
    """Fallback 1: Financial Modeling Prep"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={FMP_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'historical' in data:
            df = pd.DataFrame(data['historical'])
            df['Date'] = pd.to_datetime(df['date'])
            cutoff = datetime.now() - timedelta(days=period_days)
            df = df[df['Date'] >= cutoff].sort_values('Date')
            if not df.empty:
                df = df.rename(columns={'close': 'Close'})
                return df[['Date', 'Close']].set_index('Date')
    except Exception as e:
        print(f"FMP fallback failed for {ticker}: {e}")
    return pd.DataFrame()

def fetch_twelve_data(ticker, period_days):
    """Fallback 2: Twelve Data"""
    try:
        interval = "1day"
        url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval={interval}&outputsize=5000&apikey={TWELVE_DATA_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['Close'] = pd.to_numeric(df['close'])
            cutoff = datetime.now() - timedelta(days=period_days)
            df = df[df['datetime'] >= cutoff].sort_values('datetime')
            if not df.empty:
                return df[['datetime', 'Close']].rename(columns={'datetime': 'Date'}).set_index('Date')
    except Exception as e:
        print(f"Twelve Data fallback failed for {ticker}: {e}")
    return pd.DataFrame()

def robust_download(ticker, period, interval, attempts=2, min_rows=1):
    """Sequential Fallback Downloader: Yahoo -> FMP -> Twelve Data with timeframe reduction."""
    current_period = period
    
    while current_period:
        # 1. Try Yahoo Finance
        for i in range(attempts):
            try:
                data = yf.download(ticker, period=current_period, interval=interval, progress=False)
                if not data.empty and len(data) >= min_rows:
                    return data
            except Exception as e:
                # Catch "Period 'max' is invalid" error message
                error_msg = str(e)
                match = re.search(r"Period '(.+)' is invalid, must be one of: (.+)", error_msg)
                if match:
                    # If Yahoo tells us valid periods, use the best one
                    valid_periods = [p.strip() for p in match.group(2).split(',')]
                    # Filter our order by what Yahoo says is valid
                    for p in TIMEFRAME_ORDER:
                        if p in valid_periods:
                            current_period = p
                            break
                    else:
                        current_period = valid_periods[0]
                    break # Break retry loop to try the new valid period
            if i < attempts - 1: time.sleep(0.5)

        # 2. Try FMP/Twelve Data with current period
        days = PERIOD_TO_DAYS.get(current_period, 365)
        print(f"Yahoo failed for {ticker} ({current_period}). Trying FMP...")
        data = fetch_fmp_data(ticker, days)
        if not data.empty and len(data) >= min_rows: return data

        print(f"FMP failed for {ticker} ({current_period}). Trying Twelve Data...")
        data = fetch_twelve_data(ticker, days)
        if not data.empty and len(data) >= min_rows: return data

        # 3. If all sources failed for this period, try the next shorter period
        next_period = get_next_shorter_period(current_period)
        print(f"All sources failed for {ticker} ({current_period}). Trying next shorter: {next_period}")
        current_period = next_period

    return pd.DataFrame()

# --- Utility Functions ---

RENAME_FILE = "renamed_tickers.json"

def get_renamed_ticker(old_ticker):
    if os.path.exists(RENAME_FILE):
        with open(RENAME_FILE, 'r') as f:
            try:
                renames = json.load(f)
                return renames.get(old_ticker, old_ticker)
            except: return old_ticker
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

def resolve_ticker(ticker):
    current_ticker = get_renamed_ticker(ticker)
    data = robust_download(current_ticker, "1d", "1d", attempts=1)
    if not data.empty: return current_ticker
        
    name = find_portfolio_name(ticker)
    if name:
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={name}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            search_data = res.json()
            if search_data.get('quotes'):
                for quote in search_data['quotes']:
                    if quote.get('symbol') and quote.get('symbol') != current_ticker:
                         new_ticker = quote['symbol']
                         verify = yf.download(new_ticker, period="1d", progress=False)
                         if not verify.empty:
                             save_rename(ticker, new_ticker)
                             return new_ticker
        except Exception as e:
            print(f"Search failed for {name}: {e}")
    return current_ticker

# --- API Endpoints ---

@app.get("/api/portfolios")
def get_portfolios():
    return PORTFOLIOS

@app.get("/api/historical/{ticker}")
def get_historical(ticker: str, range: str = "5d"):
    resolved_ticker = resolve_ticker(ticker)
    cache_key = f"hist_{resolved_ticker}_{range}"
    
    interval_map = {
        "1d": "5m", "5d": "1h", "1m": "1d", "6m": "1d",
        "1y": "1d", "5y": "1wk", "10y": "1mo", "max": "1mo"
    }
    
    interval = interval_map.get(range, "1d")
    
    try:
        data = robust_download(resolved_ticker, range, interval)
            
        if data.empty:
             cached_val = cache.get(cache_key)
             if cached_val: return cached_val
             raise HTTPException(status_code=404, detail=f"No data found for ticker {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        data.reset_index(inplace=True)
        date_col = 'Date' if 'Date' in data.columns else data.columns[0]
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
        # Require at least 30 rows for analysis. Sequential fallback if needed.
        data = robust_download(resolved_ticker, "1y", "1d", min_rows=30)
        
        if data.empty:
             cached_val = cache.get(cache_key)
             if cached_val: return cached_val
             raise HTTPException(status_code=404, detail=f"No data found for analysis on {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        closes = data['Close'].dropna()
        if len(closes) < 5: 
             return {"recommendation": "Diversify", "confidence": 50, "reasons": ["Insufficient history across all sources"]}
             
        sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else closes.mean()
        sma_200 = closes.rolling(window=200).mean().iloc[-1] if len(closes) >= 200 else (closes.rolling(window=100).mean().iloc[-1] if len(closes) >= 100 else sma_50)
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
        if current_price > (sma_50 if not pd.isna(sma_50) else current_price): score += 1; reasons.append("Price is above 50-day SMA (Bullish).")
        else: score -= 1; reasons.append("Price is below 50-day SMA (Bearish).")
        
        if sma_50 > (sma_200 if not pd.isna(sma_200) else sma_50): score += 1; reasons.append("Golden Cross active (50SMA > 200SMA).")
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
                "sma50": round(float(sma_50), 2) if not pd.isna(sma_50) else round(float(current_price), 2),
                "sma200": round(float(sma_200), 2) if not pd.isna(sma_200) else round(float(sma_50), 2),
                "sharpeRatio": round(float(sharpe), 2),
                "forecast30d": round(float(forecast_price), 2)
            }
        }
        cache.set(cache_key, result, expire=3600)
        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        cached_val = cache.get(cache_key)
        if cached_val: return cached_val
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
