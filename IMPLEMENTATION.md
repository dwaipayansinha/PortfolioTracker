# Implementation Details - Portfolio Tracker

This document outlines the software architecture and the specific logic used to implement the Portfolio Tracker's core functionality.

## System Architecture

The application follows a **Decoupled Client-Server Architecture** bundled into a single desktop package.

1.  **Renderer Process (UI):** A React application that manages state and renders the dashboard.
2.  **Main Process (Electron):** Acts as the operating system bridge, handling window creation and system integration.
3.  **Sidecar API (Python):** A standalone executable that runs a FastAPI server to perform heavy data processing and AI modeling.

## AI & Analysis Logic (v2.0)

The recommendation engine uses a multi-factor scoring system to generate professional ratings.

### 1. Trend Analysis (Moving Averages)
- **Indicators:** 20-day, 50-day, and 200-day Simple Moving Averages.
- **Signals:** 
    - Price above 50-day SMA is considered a primary bullish trend.
    - Golden Cross (50-day crossing above 200-day) indicates long-term positive momentum.

### 2. Risk Assessment (Sharpe Ratio)
- **Signal:** Measures risk-adjusted return relative to portfolio volatility.
- **Threshold:** A Sharpe ratio > 0.6 contributes significantly to a "Strong Buy" rating.

### 3. ML Predictive Modeling
- **Model:** Scikit-learn Linear Regression.
- **Prediction:** Forecasts the expected price movement 30 days into the future.
- **Impact:** Significant upside potential (>2% gain) triggers a high-confidence Buy signal.

### Final Output Ratings:
- **Strong Buy:** High-confidence uptrend with low volatility.
- **Buy:** Solid positive technical indicators.
- **Hold:** Neutral or mixed signals; stability expected.
- **Sell / Strong Sell:** Negative momentum or significant downward risk detected.

## Installation & Packaging

### Professional Installer (Windows)
The software is packaged as a standard Windows NSIS installer (`.exe`). It:
- Deploys the application to the system-wide **Program Files** directory.
- Configures Start Menu and Desktop shortcuts.
- Manages the local user cache in a writable directory (`~/.portfolio_tracker`) to ensure compatibility with restricted system folders.

## Error Handling & Reliability

- **Initialization Checks:** The frontend verifies connectivity to the backend API at startup. If unreachable, a full-screen troubleshooting UI is displayed.
- **Multi-Source Fallback:** Triple-source data pipeline (Yahoo ➡️ FMP ➡️ Twelve Data).
- **Local Slicing Logic:** To ensure 100% chart consistency, the app pulls the maximum history once and slices the time windows locally on the client.
- **Persistent Data Caching:** File-based cache for offline reliability.
- **Auto-Updates:** Native background updates via GitHub Releases.
