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
warnings.filterwarnings("ignore")

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PORTFOLIOS = {
    "TD Comfort (ETF Equivalents)": {
        "TD Comfort Conservative (TCON)": "TCON.TO",
        "TD Comfort Balanced (TBAL)": "TBAL.TO",
        "TD Comfort Growth (TGRO)": "TGRO.TO",
        "TD Comfort Aggressive (TEQT)": "TEQT.TO",
    },
    "BMO (Asset Allocation)": {
        "BMO Conservative (ZCON)": "ZCON.TO",
        "BMO Balanced (ZBAL)": "ZBAL.TO",
        "BMO Growth (ZGRO)": "ZGRO.TO",
        "BMO All-Equity (ZEQT)": "ZEQT.TO",
    },
    "iShares (RBC Partner)": {
        "iShares Conservative (XCON)": "XCON.TO",
        "iShares Balanced (XBAL)": "XBAL.TO",
        "iShares Growth (XGRO)": "XGRO.TO",
        "iShares All-Equity (XEQT)": "XEQT.TO",
    },
    "Vanguard (Global Standard)": {
        "Vanguard Conservative (VCNS)": "VCNS.TO",
        "Vanguard Balanced (VBAL)": "VBAL.TO",
        "Vanguard Growth (VGRO)": "VGRO.TO",
        "Vanguard All-Equity (VEQT)": "VEQT.TO",
        "Scotia Balanced (BNS)": "BNS.TO",
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
            try:
                renames = json.load(f)
            except:
                pass
    renames[old_ticker] = new_ticker
    with open(RENAME_FILE, 'w') as f:
        json.dump(renames, f)

def find_portfolio_name(ticker):
    for bank, funds in PORTFOLIOS.items():
        for name, t in funds.items():
            if t == ticker:
                return name
    return None

def resolve_ticker(ticker):
    # Check if we already have a rename in memory
    current_ticker = get_renamed_ticker(ticker)
    
    # Try fetching small amount of data to verify if it's currently valid
    try:
        data = yf.download(current_ticker, period="1d", progress=False)
        if not data.empty:
            return current_ticker
    except:
        pass
        
    # If it failed, let's search by name
    name = find_portfolio_name(ticker)
    if name:
        try:
            # Yahoo Finance search API (internal)
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={name}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=5)
            search_data = res.json()
            if search_data.get('quotes'):
                for quote in search_data['quotes']:
                    # Look for something that matches the name closely but has a DIFFERENT symbol than our failed one
                    if quote.get('symbol') and quote.get('symbol') != current_ticker:
                         new_ticker = quote['symbol']
                         # Verify the new ticker works before committing to memory
                         verify = yf.download(new_ticker, period="1d", progress=False)
                         if not verify.empty:
                             save_rename(ticker, new_ticker)
                             return new_ticker
        except Exception as e:
            print(f"Search failed for {name}: {e}")
            
    return current_ticker # Return original (failed) ticker if no replacement found

@app.get("/api/portfolios")
def get_portfolios():
    return PORTFOLIOS

@app.get("/api/historical/{ticker}")
def get_historical(ticker: str, range: str = "1y"):
    """
    range options: 1d, 1w, 1m, 6m, 1y, 2y, 5y, 10y, max
    """
    resolved_ticker = resolve_ticker(ticker)
    
    interval_map = {
        "1d": "5m",
        "1w": "15m",
        "1m": "1d",
        "6m": "1d",
        "1y": "1d",
        "5y": "1wk",
        "10y": "1mo",
        "max": "1mo"
    }
    
    yf_period = range
    if range == "1w":
        yf_period = "5d"
        
    interval = interval_map.get(range, "1d")
    
    try:
        data = yf.download(resolved_ticker, period=yf_period, interval=interval, progress=False)
        if data.empty:
            # Fallback to daily interval if intraday fails
            data = yf.download(resolved_ticker, period=yf_period, interval="1d", progress=False)
            
        if data.empty:
             raise HTTPException(status_code=404, detail=f"No data found for ticker {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        data.reset_index(inplace=True)
        date_col = data.columns[0]
        data['time'] = data[date_col].astype(str)
        
        result = data[['time', 'Close']].rename(columns={'Close': 'value'}).dropna()
        return result.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{ticker}")
def get_analysis(ticker: str):
    """
    Hybrid analysis: Traditional + ML
    """
    resolved_ticker = resolve_ticker(ticker)
    
    try:
        # Download 2 years of daily data for analysis
        data = yf.download(resolved_ticker, period="2y", interval="1d", progress=False)
        if data.empty:
             raise HTTPException(status_code=404, detail=f"No data found for analysis on {resolved_ticker}")
             
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        closes = data['Close'].dropna()
        if len(closes) < 30: # Reduced from 50 for better availability
             return {"recommendation": "Diversify", "confidence": 50, "reasons": ["Insufficient data for full analysis"]}
             
        # Traditional Metrics
        sma_50 = closes.rolling(window=50).mean().iloc[-1] if len(closes) >= 50 else closes.mean()
        sma_200 = closes.rolling(window=200).mean().iloc[-1] if len(closes) >= 200 else sma_50
        current_price = closes.iloc[-1]
        
        returns = closes.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        annual_return = returns.mean() * 252
        sharpe = annual_return / volatility if volatility != 0 else 0
        
        # ML Forecasting
        lookback = min(100, len(closes))
        y = closes.values[-lookback:]
        X = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.array([[len(y) + 30]])
        forecast_price = model.predict(future_X)[0]
        
        # Scoring System
        score = 0
        reasons = []
        
        if current_price > sma_50:
            score += 1
            reasons.append("Price is above 50-day SMA (Bullish).")
        else:
            score -= 1
            reasons.append("Price is below 50-day SMA (Bearish).")
            
        if sma_50 > sma_200:
            score += 1
            reasons.append("Golden Cross active (50SMA > 200SMA).")
        else:
            score -= 1
            reasons.append("Death Cross active (50SMA < 200SMA).")
            
        if sharpe > 0.5:
            score += 1
            reasons.append(f"Favorable risk-adjusted returns (Sharpe: {sharpe:.2f}).")
        elif sharpe < 0:
            score -= 1
            reasons.append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f}).")
            
        if forecast_price > current_price * 1.02:
            score += 2
            reasons.append(f"ML Model forecasts >2% growth in 30 days.")
        elif forecast_price < current_price:
            score -= 2
            reasons.append(f"ML Model forecasts price drop.")
            
        # Decision
        if score >= 2:
            rec = "Invest"
            conf = min(100, 50 + score * 10)
        elif score <= -2:
            rec = "Remove"
            conf = min(100, 50 + abs(score) * 10)
        else:
            rec = "Diversify"
            conf = 60
            
        return {
            "recommendation": rec,
            "confidence": conf,
            "reasons": reasons,
            "metrics": {
                "currentPrice": round(float(current_price), 2),
                "sma50": round(float(sma_50), 2),
                "sma200": round(float(sma_200), 2),
                "sharpeRatio": round(float(sharpe), 2),
                "forecast30d": round(float(forecast_price), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
