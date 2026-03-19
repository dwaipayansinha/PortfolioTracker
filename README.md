# Canadian Bank Investment Portfolio Tracker

A modern desktop application built with Electron, React, and Python (FastAPI) to track TD, BMO, RBC, and Scotiabank portfolios, visualize their historical performance, and get AI-powered investment recommendations using a hybrid quantitative/ML approach.

## Documentation Index
For detailed technical information, please refer to the following files:
- [TECHNOLOGY.md](./TECHNOLOGY.md) - Full breakdown of the tech stack and core features.
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Deep dive into AI logic, architecture, and packaging.

## Prerequisites (for Development only)
- Node.js (v20+)
- Python (v3.12+)

## Setup

1. **Backend (Python)**
   Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install fastapi uvicorn yfinance pandas scikit-learn requests pyinstaller
   ```

2. **Frontend (Electron + React)**
   Open a second terminal and navigate to the `frontend` folder:
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

### Option 1: Using the Standalone Installer (Recommended for Users)
A fully packaged installer has been generated for Windows 10 & 11. This version bundles the Python backend and all runtimes automatically.

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

## Features
- **Big Four Coverage:** Track top portfolios from TD, BMO, RBC, and Scotiabank.
- **Interactive Charting:** View historical data over 1D, 1W (Default), 1M, 6M, 1Y, 5Y, 10Y, and Max timeframes.
- **Hybrid Analysis:** Combines Traditional Quant (SMA, Risk metrics) with ML forecasting to generate an actionable score.
- **Self-Healing:** Ticker Auto-Resolver searches for renamed portfolios automatically.
- **Error Recovery:** Integrated 60s auto-refresh and manual retry UI for data fetching.
