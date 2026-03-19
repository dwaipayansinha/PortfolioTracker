# Technological Stack - Portfolio Tracker

This document provides a detailed breakdown of the technologies used in the Canadian Bank Investment Portfolio Tracker.

## Frontend (Desktop UI)
- **Framework:** [React 18](https://reactjs.org/) with [TypeScript](https://www.typescriptlang.org/).
- **Build Tool:** [Vite](https://vitejs.dev/) for fast development and optimized production bundling.
- **Desktop Wrapper:** [Electron](https://www.electronjs.org/) to provide a native desktop experience on Windows.
- **Charting:** [Recharts](https://recharts.org/) for interactive, responsive SVG-based financial graphs.
- **Icons:** [Lucide React](https://lucide.dev/) for consistent, scalable UI iconography.
- **Styling:** Vanilla CSS with modern Flexbox and Grid layouts, featuring a high-contrast dark mode.

## Backend (AI & Data Engine)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python) for high-performance, asynchronous API endpoints.
- **Data Sourcing:** 
  - **yfinance (Primary):** For high-resolution intraday and historical market data.
  - **Financial Modeling Prep (Fallback 1):** Official REST API for TSX reliability.
  - **Twelve Data (Fallback 2):** Tertiary coverage for maximum uptime.
- **Data Science:** 
  - **Pandas & NumPy:** For time-series manipulation and statistical calculations.
  - **Scikit-learn:** Specifically used for the Linear Regression forecasting model.
- **Persistence:** 
  - **Diskcache:** For high-performance, file-based API response caching.
  - **Local JSON:** For the Ticker Auto-Resolver memory.

## Core Features
### 1. Hybrid Analysis Model
The "Strongest Output" recommendation engine combines:
- **Traditional Quantitative Analysis:** SMA (Simple Moving Averages) and Sharpe Ratio (Risk-adjusted returns).
- **Machine Learning Forecasting:** A Linear Regression model trained on recent price action to predict 30-day trends.
- **Weighted Scoring:** A logic engine that synthesizes these inputs into an Invest, Diversify, or Remove signal.

### 2. Multi-Source Fail-Safe
A robust data pipeline that:
1.  Attempts primary fetch from Yahoo Finance.
2.  Automatically falls back to FMP or Twelve Data if Yahoo is rate-limited or returns insufficient history.
3.  Ensures a minimum of 30 days of history for AI models whenever possible.
4.  Caches all successful results locally for instant subsequent loads.

### 3. Ticker Auto-Resolver
A self-healing mechanism that detects failed data fetches and automatically searches for renamed symbols.

### 4. Desktop Integration
- **Process Management:** The Electron main process handles the lifecycle of the Python backend.
- **Auto-Updates:** Integrated [electron-updater](https://www.npmjs.com/package/electron-updater) for automatic software updates via GitHub Releases.
- **Communication:** Standard REST API calls over localhost (Port 8000) with CORS protection.
