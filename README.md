# Canadian Bank Investment Portfolio Tracker (v1.3.0)

A professional desktop application built with Electron, React, and Python (FastAPI) to track TD, BMO, RBC, Scotiabank, and CIBC portfolios, featuring AI-powered investment recommendations.

## Documentation Index
- [TECHNOLOGY.md](./TECHNOLOGY.md) - Full breakdown of the multi-source tech stack.
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Deep dive into AI logic, sequential startup, and Program Files deployment.

## Installation & User Guide (Windows 10/11)

### 1. Professional Installation (Recommended)
This method installs the software to `C:\Program Files` and creates desktop/start menu shortcuts.

**Steps:**
1.  Navigate to the project root directory.
2.  Right-click **`Install-PortfolioTracker.ps1`** and select **"Run with PowerShell"**.
3.  Accept the Administrator prompt if asked.
4.  Once complete, launch **"Portfolio Tracker"** from your Desktop or Start Menu.

### 2. Manual/Portable Use
You can run the application directly without installing:
- **Path:** `frontend/release/win-unpacked/Portfolio Tracker.exe`
- **Behavior:** The app will automatically spawn the Python backend in the background and perform a health check before showing the GUI.

## Core Features
- **Sequential Startup**: Backend starts first with an automated health check before the GUI appears.
- **Program Files Support**: Dedicated installer script for standard Windows deployment.
- **Fail-Safe Data**: Triple-API fallback (Yahoo -> FMP -> Twelve Data).
- **Sequential History**: Intelligent timeframe fallback (Max -> 10Y -> ... -> 1D).
- **AI Recommendation Engine**: Hybrid Quant/ML models for Invest/Remove signals.
- **Persistent Cache**: Offline reliability via disk-based data storage.
- **Auto-Updates**: Checks for newer versions on startup via GitHub.

## Android Application (Mobile)
Supports **Free** (Ad-supported) and **Paid** (Ad-free) variants.
Refer to [IMPLEMENTATION.md](./IMPLEMENTATION.md) for mobile build instructions.
