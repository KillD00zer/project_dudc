---
title: Running Tests & Diagnostics
tags: [testing, diagnostics, commands, troubleshooting]
related_files:
  - tests/
  - requirements.txt
---

# 🧪 Running Tests & Diagnostics

---

## 🚀 Executing the Test Suite

From the project root directory:

```powershell
# Run the entire test suite using Python with installed dependencies:
python -m unittest discover -s tests -p "test_*.py"
```

### Running Individual Test Modules
```powershell
# Test Geodesic Calculations & Survey Ingestion:
python -m unittest tests/test_geo.py

# Test Center Normalization:
python -m unittest tests/test_jurisdictions.py

# Test CAD Croquis Rendering:
python -m unittest tests/test_croquis.py

# Test Folder Explorer:
python -m unittest tests/test_folder_explorer.py

# Test REST Endpoints:
python -m unittest tests/test_endpoints.py
```

---

## ⚠️ Troubleshooting Missing Dependencies

If tests report:
```text
ModuleNotFoundError: No module named 'pandas'
```
or missing `shapely`, `pyproj`, `matplotlib`:

1. **Portable Runtime (Recommended):**
   Run [`Setup_Portable_Runtime.bat`](file:///d:/Work/certi_processing_tools/project_dudc/Setup_Portable_Runtime.bat) to download and configure the self-contained 32-bit Python 3.11 environment with all pre-compiled wheels in `DUDC V3/runtime/`.
   Then run tests using the portable python:
   ```powershell
   "DUDC V3\runtime\python.exe" -m unittest discover -s tests -p "test_*.py"
   ```

2. **System Python / Virtual Environment:**
   Run [`Install_Dependencies.bat`](file:///d:/Work/certi_processing_tools/project_dudc/Install_Dependencies.bat) or:
   ```powershell
   pip install -r requirements.txt
   ```

