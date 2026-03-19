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
from datetime import datetime, timedelta, timezone
import time
import re
from pathlib import Path

warnings.filterwarnings("ignore")

# Setup persistent data directory in the user's home folder
DATA_DIR = Path.home() / ".portfolio_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

# Setup persistent disk cache
# BUMPED CACHE VERSION TO FORCE REFRESH FOR USER
cache = diskcache.Cache(str(DATA_DIR / "api_cache_v2"))

# API Keys
FMP_API_KEY = "gjKkPLDKVAvvtXON3D9Yfvij9dZI9Ibo"
TWELVE_DATA_API_KEY = "e60c246821d8495c8553022f50b404d8"

# Allow CORS
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

PERIOD_TO_DAYS = {
    "1d": 1, "5d": 7, "1m": 31, "6m": 183, "1y": 366, "5y": 1826, "10y": 3653, "max": 99999
}

# --- Data Fetchers ---

def fetch_fmp_max(ticker):
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={FMP_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'historical' in data:
            df = pd.DataFrame(data['historical'])
            df['Date'] = pd.to_datetime(df['date'])
            df = df.sort_values('Date')
            return df.rename(columns={'close': 'Close'}).set_index('Date')
    except: pass
    return pd.DataFrame()

def fetch_twelve_max(ticker):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={ticker}&interval=1day&outputsize=5000&apikey={TWELVE_DATA_API_KEY}"
        res = requests.get(url, timeout=10)
        data = res.json()
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df['Date'] = pd.to_datetime(df['datetime'])
            df['Close'] = pd.to_numeric(df['close'])
            df = df.sort_values('Date')
            return df.set_index('Date')
    except: pass
    return pd.DataFrame()

def get_max_data(ticker):
    """Always pull MAX history from available sources."""
    # 1. Yahoo
    try:
        data = yf.download(ticker, period="max", interval="1d", progress=False)
        if not data.empty: return data
    except: pass

    # 2. FMP
    data = fetch_fmp_max(ticker)
    if not data.empty: return data

    # 3. Twelve Data
    data = fetch_twelve_max(ticker)
    return data

# --- API Endpoints ---

@app.get("/api/portfolios")
def get_portfolios():
    return PORTFOLIOS

@app.post("/api/clear-cache")
def clear_cache():
    cache.clear()
    return {"status": "success"}

@app.get("/api/data/{ticker}")
def get_full_portfolio_data(ticker: str):
    cache_key = f"full_data_v2_{ticker}"
    cached = cache.get(cache_key)
    if cached: return cached

    data = get_max_data(ticker)
    if data.empty:
        raise HTTPException(status_code=404, detail="No data found")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    data.reset_index(inplace=True)
    date_col = 'Date' if 'Date' in data.columns else data.columns[0]
    
    # Process for JSON
    data['time'] = data[date_col].astype(str)
    data['value'] = pd.to_numeric(data['Close'], errors='coerce')
    series = data[['time', 'value']].dropna().to_dict(orient='records')

    # Calculate Availability
    first_date = pd.to_datetime(series[0]['time'])
    if first_date.tzinfo:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()
    
    total_days = (now - first_date.replace(tzinfo=None) if first_date.tzinfo else now - first_date).days
    availability = {p: (total_days >= days * 0.8) for p, days in PERIOD_TO_DAYS.items()}
    availability['max'] = True

    # --- PROFESSIONAL AI ANALYSIS (v2) ---
    closes = data['value'].dropna()
    analysis = {}
    if len(closes) > 10:
        # Metrics Calculation
        current_price = float(closes.iloc[-1])
        sma_20 = float(closes.rolling(window=min(20, len(closes))).mean().iloc[-1])
        sma_50 = float(closes.rolling(window=min(50, len(closes))).mean().iloc[-1])
        sma_200 = float(closes.rolling(window=min(200, len(closes))).mean().iloc[-1])
        
        # Risk Metric (Annualized Sharpe Proxy)
        returns = closes.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        sharpe = (returns.mean() * 252) / volatility if volatility > 0.0001 else 0
        
        # ML Forecast
        lookback = min(100, len(closes))
        y = closes.values[-lookback:]
        X = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        forecast = float(model.predict(np.array([[len(y) + 30]]))[0])
        forecast_pct = (forecast - current_price) / current_price
        
        score = 0
        reasons = []
        
        # 1. Trend Analysis (Moving Averages)
        if current_price > sma_50:
            score += 2
            reasons.append(f"Price (${current_price:.2f}) is above 50-day average (${sma_50:.2f}), confirming a bullish trend.")
        else:
            score -= 2
            reasons.append(f"Price (${current_price:.2f}) is below 50-day average (${sma_50:.2f}), indicating bearish pressure.")
            
        if sma_50 > sma_200:
            score += 1
            reasons.append("Golden Cross confirmed: Long-term momentum is positive.")
        elif sma_50 < sma_200:
            score -= 1
            reasons.append("Death Cross active: Long-term momentum is negative.")

        # 2. Risk/Reward (Sharpe Ratio)
        if sharpe > 0.6:
            score += 2
            reasons.append(f"High risk-adjusted performance (Sharpe: {sharpe:.2f}).")
        elif sharpe < 0:
            score -= 1
            reasons.append(f"Negative risk-adjusted returns (Sharpe: {sharpe:.2f}).")

        # 3. AI Predictive Modeling
        if forecast_pct > 0.02:
            score += 3
            reasons.append(f"AI Model signals strong upside potential of {forecast_pct*100:.1f}% over the next 30 days.")
        elif forecast_pct > 0.005:
            score += 1
            reasons.append(f"AI Model predicts steady growth (~{forecast_pct*100:.1f}%) in the short term.")
        elif forecast_pct < -0.02:
            score -= 3
            reasons.append(f"AI Model detects significant downward risk ({forecast_pct*100:.1f}%) ahead.")

        # FINAL RATING
        if score >= 4: rec = "Strong Buy"
        elif score >= 1: rec = "Buy"
        elif score >= -1: rec = "Hold"
        elif score >= -3: rec = "Sell"
        else: rec = "Strong Sell"
        
        analysis = {
            "recommendation": rec,
            "confidence": min(98, 60 + abs(score) * 6),
            "reasons": reasons,
            "metrics": {
                "currentPrice": round(current_price, 2),
                "forecast30d": round(forecast, 2),
                "sma50": round(sma_50, 2),
                "sharpeRatio": round(sharpe, 2)
            }
        }

    response = {
        "series": series,
        "availability": availability,
        "analysis": analysis
    }
    
    cache.set(cache_key, response, expire=3600)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
