# Technological Stack - Portfolio Tracker

This document provides a detailed breakdown of the technologies used in the Canadian Bank Investment Portfolio Tracker.

## Frontend (Desktop UI)
- **Framework:** [React 18](https://reactjs.org/) with [TypeScript](https://www.typescriptlang.org/).
- **Build Tool:** [Vite](https://vitejs.dev/) for optimized production bundling.
- **Desktop Wrapper:** [Electron](https://www.electronjs.org/) to provide a native desktop experience on Windows.
- **Charting:** [Recharts](https://recharts.org/) for interactive, responsive SVG-based financial graphs.
- **Icons:** [Lucide React](https://lucide.dev/) for consistent UI iconography.
- **Styling:** Vanilla CSS with modern Flexbox and Grid layouts, featuring a dark mode theme.

## Backend (AI & Data Engine)
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python) for high-performance API endpoints.
- **Data Sourcing:** 
  - **yfinance (Primary):** For historical market data.
  - **Financial Modeling Prep (Fallback 1):** Official REST API for TSX reliability.
  - **Twelve Data (Fallback 2):** Tertiary coverage for maximum uptime.
- **Data Science:** 
  - **Pandas & NumPy:** For time-series manipulation and statistical calculations.
  - **Scikit-learn:** Specifically used for the Linear Regression forecasting model.
- **Persistence:** 
  - **Diskcache:** For high-performance, file-based API response caching.
  - **Local JSON:** For internal configuration and memory.

## Core Features
### 1. Advanced AI Analysis
The recommendation engine analyzes portfolios using several key indicators:
- **Trend Confirmation:** Comparison of current price against 20-day, 50-day, and 200-day Simple Moving Averages (SMA).
- **Machine Learning Forecast:** A Linear Regression model trained on recent price action to predict 30-day trends.
- **Risk Assessment:** Calculation of the Sharpe Ratio to evaluate risk-adjusted performance.
- **Professional Ratings:** Signals include "Strong Buy", "Buy", "Hold", "Sell", and "Strong Sell".

### 2. Multi-Source Fail-Safe
A robust data pipeline that:
1.  Attempts primary fetch from Yahoo Finance (Max period).
2.  Automatically falls back to FMP or Twelve Data if Yahoo is rate-limited or unavailable.
3.  Caches all successful results locally in a persistent versioned cache.

### 3. Desktop Integration
- **Auto-Updates:** Integrated [electron-updater](https://www.npmjs.com/package/electron-updater) for automatic software updates via GitHub Releases.
- **Stability:** Hardware acceleration disabled to ensure compatibility across all Windows graphics hardware.
