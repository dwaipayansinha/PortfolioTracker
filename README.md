# Canadian Bank Investment Portfolio Tracker

A modern desktop application built with Electron, React, and Python (FastAPI) to track TD Comfort Portfolios, visualize their historical performance, and get AI-powered investment recommendations using a hybrid quantitative/ML approach.

## Prerequisites
- Node.js (v20+)
- Python (v3.12+)

## Setup

1. **Backend (Python)**
   Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt # (or just install fastapi uvicorn yfinance pandas scikit-learn)
   ```

2. **Frontend (Electron + React)**
   Open a second terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

### Option 1: Using the Standalone Installer (Recommended)
A fully packaged installer has been generated for Windows 11. This version bundles the Python backend and all runtimes automatically.

**Installer Location:**
`frontend/out/make/squirrel.windows/x64/portfolio-tracker-1.0.0 Setup.exe`

Run this file on any Windows computer to install the Portfolio Tracker as a standard desktop application.

### Option 2: Running from Source (Development)
You need to run both the backend and the frontend concurrently.

**Step 1:** Start the Python Backend
```bash
cd backend
.\venv\Scripts\activate
python main.py
```
*(The API will start at http://127.0.0.1:8000)*

**Step 2:** Start the Electron Frontend
In a new terminal:
```bash
cd frontend
npm run dev
```

The Electron window will appear, fetching portfolio data from Yahoo Finance and generating real-time recommendations based on Moving Averages, Sharpe Ratios, and a lightweight Machine Learning model.

## Features
- **Interactive Charting:** View historical data over 1D, 1W, 1M, 6M, 1Y, 5Y, 10Y, and Max timeframes.
- **Hybrid Analysis:** Combines Traditional Quant (SMA, Risk metrics) with ML forecasting to generate an actionable score.
- **Recommendations:** Outputs an Invest, Diversify, or Remove signal along with confidence percentage and detailed reasoning.
