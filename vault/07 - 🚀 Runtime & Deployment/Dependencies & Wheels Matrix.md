---
title: Dependencies & Wheels Matrix
tags: [deployment, dependencies, wheels, python, 32-bit]
related_files:
  - requirements.txt
  - DUDC V3/requirements.txt
---

# 🚀 Dependencies & Wheels Matrix

File: [`requirements.txt`](file:///d:/Work/certi_processing_tools/project_dudc/requirements.txt)

The dependency matrix accounts for both standard 64-bit systems and legacy 32-bit (x86) Windows workstations.

---

## 📦 Package Matrix & Version Constraints

| Package Name | Architecture | Version Specification | Purpose |
|---|---|---|---|
| `numpy` | x86 (32-bit)<br>x64 (64-bit) | `>=1.24.0, <2.0.0` (pinned to `1.26.4`)<br>`>=1.24.0` | Matrix math, polygon centroid & scaling |
| `pandas` | x86 (32-bit)<br>x64 (64-bit) | `>=2.0.0, <=2.0.3`<br>`>=2.0.0` | Excel / CSV data table ingestion |
| `openpyxl` | All | `>=3.1.0` | Modern Excel `.xlsx` reader |
| `xlrd` | All | `>=2.0.1` | Legacy Excel `.xls` reader |
| `pyproj` | All | `>=3.5.0` | WGS84 geodesic calculations via PROJ C-API |
| `shapely` | All | `>=2.0.0` | GEOS polygon operations and geometry handling |
| `pillow` | All | `>=10.0.0` | Tile stitching, image manipulation & alpha composite |
| `matplotlib` | x86 (32-bit)<br>x64 (64-bit) | `>=3.7.0, <=3.7.5`<br>`>=3.7.0` | CAD Croquis vector drawing (Agg backend) |
| `kiwisolver` | x86 (32-bit) | `<=1.4.7` | Matplotlib constraint layout solver |
| `arabic-reshaper` | All | `>=3.0.0` | Arabic glyph contextual reshaping |
| `python-bidi` | x86 (32-bit)<br>x64 (64-bit) | `>=0.4.2, <0.5.0` (pinned to `0.4.2`)<br>`>=0.4.2` | Bidirectional layout algorithm for Arabic text |

---

## 💡 Notes on Python 3.12+ and 3.14 Compatibility
- Python 3.14 (pre-release) removes or alters certain C-API internals; pre-compiled wheels for `numpy`, `shapely`, and `pyproj` are currently distributed primarily for Python $3.9 \dots 3.12$.
- The bundled portable runtime runs on **Python 3.11.9 32-bit**, guaranteeing 100% binary stability across all Windows machines.

