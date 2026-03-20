# Canadian Bank Investment Portfolio Tracker (v1.5.0)

A professional desktop application built with Electron, React, and Python (FastAPI) to track TD, BMO, RBC, Scotiabank, and CIBC portfolios, featuring AI-powered investment recommendations.

## Documentation Index
- [TECHNOLOGY.md](./TECHNOLOGY.md) - Full breakdown of the multi-source tech stack.
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Deep dive into AI logic, local slicing architecture, and packaging.

## Installation & User Guide (Windows 10/11)

### 1. Professional Installation (Recommended)
This method installs the software to `C:\Program Files` and creates desktop/start menu shortcuts.

**Steps:**
1.  Download the latest **`Portfolio Tracker Setup 1.5.0.exe`** from the GitHub Releases page.
2.  Run the setup file and accept the Administrator prompt.
3.  Once complete, launch **"Portfolio Tracker"** from your Desktop or Start Menu.
4.  **Note**: On first launch, click **"Clear Cache"** in the sidebar to initialize the AI engine.

### 2. Development Setup
If you wish to run the project from source:

**Backend:**
```bash
cd backend
.\venv\Scripts\activate
python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## Core Features
- **Professional AI Ratings**: Industry-standard signals (Strong Buy, Buy, Hold, Sell, Strong Sell).
- **In-Depth Analysis Breakdown**: Bulleted insights explaining the trend, momentum, and forecast for every fund.
- **Fail-Safe Data Engine**: Triple-source fallback (Yahoo ➡️ FMP ➡️ Twelve Data) ensuring near-100% uptime.
- **Dynamic Trend Lines**: High-visibility dashed overlays showing AI-predicted price direction.
- **Local Slicing Technology**: Pulls maximum history once to ensure instantaneous and consistent chart switching.
- **Stability Focused**: Custom rendering configuration to prevent black screens and driver conflicts.
- **Persistent Failover Cache**: Automatically displays last known data if APIs are unreachable.
- **Auto-Updates**: Seamless background updates via GitHub.
