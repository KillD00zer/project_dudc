---
title: Portable Zero-Install Runtime Design
tags: [architecture, runtime, portable, python311, batch]
related_files:
  - Setup_Portable_Runtime.bat
  - DUDC V3/Setup_Portable_Runtime.bat
  - Run_DUDC_V4.bat
  - DUDC V3/Run_DUDC_V4.bat
  - requirements.txt
---

# 📦 Portable Zero-Install Runtime Design

Cadastral surveyors and engineers often operate on workstations with varying configurations:
- Legacy Windows 7, Windows 10, or Windows 11.
- Both 32-bit (x86) and 64-bit architectures with restricted RAM (e.g. 4GB).
- Strict IT policies (AppLocker, Group Policy restrictions against installing software).
- Air-gapped or unstable internet connections.

To address these constraints, DUDC V4.0 features a **Zero-Install, Zero-Internet Portable Runtime Architecture**.

---

## 🛠️ Architecture Components

```text
DUDC V3/
├── runtime/                             # Embedded Python 3.11 32-bit Runtime
│   ├── python.exe                       # Standalone binary (no registry dependency)
│   ├── python311.dll
│   ├── python311._pth                   # Custom path configuration
│   └── Lib/
│       └── site-packages/               # Pre-compiled C-extensions (NumPy, Shapely, PyProj, Pandas)
├── Run_DUDC_V4.bat                      # Top-priority portable launcher
└── Setup_Portable_Runtime.bat           # Automated environment provisioner
```

---

## ⚙️ Path Resolution in `python311._pth`
By default, Windows Python embeddable distributions isolate themselves completely and ignore `site-packages` or the parent directory.
The setup script configures `python311._pth` as follows:
```text
python311.zip
.
# enable site-packages
import site
..
Lib\site-packages
```
This enables full access to installed mathematical wheels and allows importing `core_gis` and `server` packages seamlessly.

---

## 🔍 Priority Order in `Run_DUDC_V4.bat`
When `Run_DUDC_V4.bat` executes, it detects Python using a strict cascade:
1. **Top Priority:** Pre-bundled portable 32-bit runtime in `./runtime/python.exe` or `../runtime/python.exe`.
2. **Second Priority:** ArcGIS Pro bundled Python environment (`C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`).
3. **Third Priority:** System Python on PATH (`python.exe` or `py.exe`).
4. **Fourth Priority:** Scans standard local user directories (`%LOCALAPPDATA%\Programs\Python\Python3*`, `C:\Python3*`, `%ProgramFiles%\Python3*`).

If a portable runtime is active, dependency checks and internet pip installations are safely bypassed, achieving an instant (< 0.5s) startup time.

