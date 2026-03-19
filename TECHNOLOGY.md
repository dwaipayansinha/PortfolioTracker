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
- **Data Sourcing:** [yfinance](https://github.com/ranaroussi/yfinance) for fetching live and historical market data from Yahoo Finance.
- **Data Science:** 
  - **Pandas & NumPy:** For time-series manipulation and statistical calculations.
  - **Scikit-learn:** Specifically used for the Linear Regression forecasting model.
- **Persistence:** Local JSON storage (`renamed_tickers.json`) for the Ticker Auto-Resolver memory.

## Core Features
### 1. Hybrid Analysis Model
The "Strongest Output" recommendation engine combines:
- **Traditional Quantitative Analysis:** SMA (Simple Moving Averages) and Sharpe Ratio (Risk-adjusted returns).
- **Machine Learning Forecasting:** A Linear Regression model trained on recent price action to predict 30-day trends.
- **Weighted Scoring:** A logic engine that synthesizes these inputs into an Invest, Diversify, or Remove signal.

### 2. Ticker Auto-Resolver
A self-healing mechanism that:
1. Detects failed data fetches.
2. Automatically searches Yahoo Finance for renamed or updated symbols by fund name.
3. Verifies the new ticker and caches it for future use.

### 3. Desktop Integration
- **Process Management:** The Electron main process handles the lifecycle of the Python backend, spawning it on launch and terminating it on quit.
- **Auto-Updates:** Integrated [electron-updater](https://www.npmjs.com/package/electron-updater) for automatic software updates via GitHub Releases.
- **Communication:** Standard REST API calls over localhost (Port 8000) with CORS protection.
