---
title: Startup Scripts & Shortcuts
tags: [deployment, runtime, batch, shortcuts, windows]
related_files:
  - Run_DUDC_V4.bat
  - DUDC V3/Run_DUDC_V4.bat
  - Setup_Portable_Runtime.bat
  - Update_DUDC_V4.bat
---

# 🚀 Startup Scripts & Shortcuts

The project includes batch scripts designed to handle Windows shortcut automation, process cleanup, Python detection, and browser launching.

---

## 📜 Script Inventory

### 1. `Run_DUDC_V4.bat` (Root Launcher)
- Automatically checks for the presence of the desktop shortcut `DUDC V4 Studio.lnk`. If missing, creates it using a PowerShell `WScript.Shell` COM object, assigning `DUDC V3\assets\app_icon.ico`.
- Navigates to `DUDC V3/` and launches the modular application runner.

### 2. `DUDC V3/Run_DUDC_V4.bat` (Master Engine Launcher)
- **Port Conflict Buster:** Scans `netstat -ano` for any stale process listening on `127.0.0.1:8765` and forces termination via `taskkill /f /pid <pid>`.
- **Git Discovery:** Appends common Git install directories to `PATH` if Git is not already available.
- **Python Cascading Probe:**
  1. Checks for portable runtime at `runtime\python.exe` or `..\runtime\python.exe`.
  2. Checks for ArcGIS Pro bundled Python (`arcgispro-py3`).
  3. Checks `python` or `py` in system PATH.
  4. Scans user and system directories (`%LOCALAPPDATA%\Programs\Python\...`, `C:\Python3*`).
  - **Dependency Self-Healing:** If running on system Python without the portable runtime, verifies required packages and runs `pip install -r requirements.txt` automatically if any are missing.
- **Server Bootstrap:** Launches `app_server.py`.

### 3. `Setup_Portable_Runtime.bat`
- Automatically provisions an isolated 32-bit Python 3.11 embeddable environment in `DUDC V3/runtime/`.
- Configures `python311._pth` to import `Lib\site-packages` and the project root.
- Bootstraps pip via `get-pip.py`.
- Installs pre-compiled 32-bit math and GIS wheels.

### 4. `Update_DUDC_V4.bat`
- Shortcut that runs `git pull origin main` to pull the latest updates directly from GitHub.

