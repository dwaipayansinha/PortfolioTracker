# Canadian Bank Investment Portfolio Tracker (v1.1.0)

A modern desktop application built with Electron, React, and Python (FastAPI) to track TD, BMO, RBC, Scotiabank, and CIBC portfolios, visualize their historical performance, and get AI-powered investment recommendations using a hybrid quantitative/ML approach.

## Documentation Index
For detailed technical information, please refer to the following files:
- [TECHNOLOGY.md](./TECHNOLOGY.md) - Full breakdown of the multi-source tech stack.
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Deep dive into AI logic, fallback architecture, and packaging.

## Installation & User Guide

### 1. Using the Standalone Installer (Recommended)
The project includes a fully packaged installer for **Windows 10 & 11**. This version is completely standalone and does not require Python or Node.js.

**Installer Location:**
`frontend/out/make/squirrel.windows/x64/portfolio-tracker-1.1.0 Setup.exe`

**Installation Steps:**
1.  **Run the Setup**: Double-click the `.exe` file.
2.  **Security Note**: Since this is a private build, Windows may show a "Windows protected your PC" popup. Click **"More info"** and then **"Run anyway"**.
3.  **Automatic Setup**: The app installs automatically to your local user directory and creates shortcuts.
4.  **Auto-Updates**: The app will automatically check for and install newer versions on startup.

### 2. Running from Source (Development)
If you wish to modify the code:

**Step 1: Start the Python Backend**
```bash
cd backend
.\venv\Scripts\activate
python main.py
```

**Step 2: Start the Electron Frontend**
```bash
cd frontend
npm run dev
```

## Core Features
- **Big Five Coverage:** Complete tracking for TD, BMO, RBC, Scotiabank, and CIBC suites.
- **Fail-Safe Data:** Triple-API fallback (Yahoo -> FMP -> Twelve Data) ensuring maximum uptime.
- **Hybrid Analysis:** Combines Moving Averages and Sharpe Ratios with Machine Learning price forecasting.
- **Persistent Cache:** Displays last successful data even when offline or rate-limited.
- **Auto-Updates:** Native background updates via GitHub Releases.
- **Self-Healing:** Automatic ticker resolution for renamed or retired funds.
