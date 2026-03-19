# Canadian Bank Investment Portfolio Tracker (v1.5.0)

A professional desktop application built with Electron, React, and Python (FastAPI) to track TD, BMO, RBC, Scotiabank, and CIBC portfolios, featuring AI-powered investment recommendations.

## Documentation Index
- [TECHNOLOGY.md](./TECHNOLOGY.md) - Full breakdown of the multi-source tech stack.
- [IMPLEMENTATION.md](./IMPLEMENTATION.md) - Deep dive into AI logic, sequential startup, and Program Files deployment.

## Installation & User Guide (Windows 10/11)

### 1. Professional Installation (Recommended)
This method installs the software to `C:\Program Files` and creates desktop/start menu shortcuts.

**Steps:**
1.  Download the latest **`Portfolio Tracker Setup 1.5.0.exe`** from the GitHub Releases page.
2.  Run the setup file.
3.  Accept the Administrator prompt if asked.
4.  Once complete, launch **"Portfolio Tracker"** from your Desktop or Start Menu.

### 2. Manual/Portable Use
You can run the application directly from the source if you have the dependencies installed.
Refer to [IMPLEMENTATION.md](./IMPLEMENTATION.md) for details.

## Core Features
- **Professional AI Ratings**: Uses industry-standard terms (Strong Buy, Buy, Hold, Sell, Strong Sell).
- **Detailed Analysis Breakdown**: Explains the logic behind every recommendation.
- **Fail-Safe Data**: Triple-API fallback (Yahoo -> FMP -> Twelve Data).
- **Sequential History**: Intelligent timeframe fallback (Max -> 10Y -> ... -> 1D).
- **Persistent Cache**: Offline reliability via disk-based data storage.
- **Auto-Updates**: Checks for newer versions on startup via GitHub.

## Android Application (Mobile)
Supports **Free** (Ad-supported) and **Paid** (Ad-free) variants.
Refer to [IMPLEMENTATION.md](./IMPLEMENTATION.md) for mobile build instructions.
