# Implementation Details - Portfolio Tracker

This document outlines the software architecture and the specific logic used to implement the Portfolio Tracker's core functionality.

## System Architecture

The application follows a **Decoupled Client-Server Architecture** bundled into a single desktop package.

1.  **Renderer Process (UI):** A React application that manages state and renders the dashboard.
2.  **Main Process (Electron):** Acts as the operating system bridge, handling window creation and backend process management.
3.  **Sidecar API (Python):** A standalone executable (compiled with PyInstaller) that runs a FastAPI server to perform heavy data processing and AI modeling.

## AI & Analysis Logic

The recommendation engine uses a weighted scoring system (Score range: -5 to +5).

### 1. Simple Moving Averages (SMA)
- **Signal:** Comparison of Current Price vs. 50-day SMA and 50-day SMA vs. 200-day SMA.
- **Logic:** Price > SMA50 is Bullish (+1). SMA50 > SMA200 (Golden Cross) is Bullish (+1). Opposite cases are Bearish (-1).

### 2. Risk Metric (Sharpe Ratio)
- **Signal:** Annualized risk-adjusted return.
- **Logic:** Sharpe > 0.4 adds to the "Invest" confidence. Sharpe < 0 suggests the fund is not returning enough for its volatility.

### 3. ML Trend Forecasting
- **Model:** Scikit-learn Linear Regression.
- **Training:** Trained on the most recent 100 days of closing prices.
- **Prediction:** Forecasts the price 30 days into the future.
- **Impact:** If forecasted growth is >1.5%, the score receives a high-weight boost (+2).

### Final Recommendation Output:
- **Invest:** Score >= 2
- **Remove:** Score <= -2
- **Diversify:** Score between -1 and 1

## Software Packaging & Platforms

### Desktop (Windows)
1.  **Backend Bundling:** PyInstaller bundles the Python interpreter and all libraries into `portfolio_api.exe`.
2.  **Frontend Bundling:** Vite compiles the React app into optimized static assets.
3.  **Electron Forge:** Combines the UI assets and the backend executable into a final package.
4.  **Resource Management:** The backend executable is placed in the `extraResources` folder. At runtime, the Electron Main process locates this file and spawns it.

### Mobile (Android)
1.  **Wrapper:** [Capacitor] acts as a bridge between the React web app and the Android OS.
2.  **Cloud Dependency:** Unlike the desktop version, the Android app requires a cloud-hosted backend (e.g., Render) as it cannot run a local Python server.
3.  **Build Variants:**
    - **Free Variant**: Injected with `VITE_APP_VARIANT=free`. Displays a bottom-anchored AdMob banner.
    - **Paid Variant**: Injected with `VITE_APP_VARIANT=paid`. Omit ads entirely for a premium experience.
4.  **AdMob Integration**: The `@capacitor-community/admob` plugin is initialized only in the free variant to optimize battery and data usage.

## Error Handling & Reliability

- **Multi-Source Fallback:** If the primary data source (Yahoo Finance) is rate-limited or provides "Insufficient History" (less than 30 days), the system automatically falls back to **Financial Modeling Prep** and then **Twelve Data** to satisfy the requirements of the AI models.
- **Persistent Data Caching:** The backend implements a file-based cache using `diskcache`. Successful API responses are stored locally and serve as a "graceful fallback" if all network requests fail.
- **Auto-Retry:** A `useEffect` hook in React manages a 60-second countdown timer that automatically triggers a re-fetch upon failure.
- **Ticker Resolver:** If the API returns no data, the backend initiates a name-based search to find if the fund has transitioned to a new symbol.
- **Auto-Refresh Logic:** The frontend includes an hourly timer that automatically triggers a background data refresh for the active portfolio.
- **Software Updates:** The Electron main process utilizes `electron-updater` to check for new releases on GitHub. If an update is available, it is automatically downloaded and installed.
