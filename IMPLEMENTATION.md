# Implementation Details - Portfolio Tracker

This document outlines the software architecture and the specific logic used to implement the Portfolio Tracker's core functionality.

## System Architecture

The application follows a **Decoupled Client-Server Architecture** bundled into a single desktop package.

1.  **Renderer Process (UI):** A React application that manages state and renders the dashboard.
2.  **Main Process (Electron):** Acts as the operating system bridge, handling window creation and backend process management.
3.  **Sidecar API (Python):** A standalone executable (compiled with PyInstaller) that runs a FastAPI server.

## Launch & Lifecycle Management (v1.3.0)

To ensure maximum reliability, the application implements a **Sequential Startup Sequence**:

1.  **Backend Spawning:** The Electron Main process first spawns the `portfolio_api.exe`.
2.  **Health Check:** The app performs a silent internal health check (polling the API).
3.  **UI Initialization:** The GUI window is only shown *after* the backend is confirmed as ready and responsive.
4.  **Graceful Exit:** Closing the application automatically kills the background Python process to prevent "Zombie" backend processes.

## AI & Analysis Logic

The recommendation engine uses a weighted scoring system (Score range: -5 to +5).

### 1. Simple Moving Averages (SMA)
- **Signal:** Comparison of Current Price vs. 50-day SMA and 50-day SMA vs. 200-day SMA.
- **Logic:** Price > SMA50 (+1). SMA50 > SMA200 (Golden Cross) (+1).

### 2. Risk Metric (Sharpe Ratio)
- **Signal:** Annualized risk-adjusted return.
- **Logic:** Sharpe > 0.4 adds to the "Invest" confidence.

### 3. ML Trend Forecasting
- **Model:** Scikit-learn Linear Regression.
- **Prediction:** Forecasts the price 30 days into the future.
- **Impact:** If forecasted growth is >1.5%, the score receives a high-weight boost (+2).

## Installation & Packaging

### Professional Installer (Windows)
The software is designed to reside in **`C:\Program Files\Portfolio Tracker`**. Due to standard Windows security policies, we provide a **PowerShell Installer Script (`Install-PortfolioTracker.ps1`)** that:
- Requests Administrator elevation.
- Safely deploys the application to the system-wide Program Files directory.
- Configures Start Menu and Desktop shortcuts for all users.

### Mobile (Android)
- **Wrapper:** [Capacitor] ports the React dashboard to Android.
- **Build Variants:** Supports **Free** (Ad-supported) and **Paid** (Premium) versions.

## Error Handling & Reliability

- **Multi-Source Fallback:** Triple-source data pipeline (Yahoo ➡️ FMP ➡️ Twelve Data).
- **Sequential History:** Intelligent fallback for new funds (tries Max ➡️ 10Y ➡️ ... ➡️ 1D automatically).
- **Persistent Data Caching:** File-based cache using `diskcache` for offline reliability.
- **Auto-Updates:** Native background updates via GitHub Releases.
