---
title: Developer Decision Matrix
tags: [decision-matrix, routing, fast-lookup, developer-guide]
type: matrix
last_updated: 2026-11-07
---

# 🎯 Developer Decision Matrix (Instant Target Routing)

Use this table to immediately identify which source files and functions need modification for any given prompt or bug report.

| User Request / Modification Goal | Target File(s) | Function / Class / Selector |
|---|---|---|
| **Change Area Tolerance Calculation or Limit ($\pm 2.00\text{ m}^2$)** | `DUDC V3/core_gis/geo.py` | `validate_and_enrich_parcel()` |
| **Change Excel/CSV parsing, column headers, or fuzzy matching** | `DUDC V3/core_gis/geo.py` | `read_survey_file()` & `find_col()` |
| **Fix coordinate jitter deduplication or ring closure** | `DUDC V3/core_gis/geo.py` | `read_survey_file()` (lines 170-186) |
| **Modify CAD Croquis colors, line thickness, node style** | `DUDC V3/core_gis/croquis.py` | `generate_croquis_image()` |
| **Modify CAD Croquis font sizes or inside/outside offsets** | `DUDC V3/core_gis/croquis.py` | `generate_croquis_image()` & `in_nx`, `out_nx` |
| **Change Arabic text shaping or BiDi behavior in sketches** | `DUDC V3/core_gis/croquis.py` | `shape_ar()` & `HAS_NATIVE_BIDI` |
| **Adjust Google Satellite zoom calculation or tile fetching** | `DUDC V3/core_gis/satellite.py` | `determine_zoom()` & `fetch_tile()` |
| **Modify Satellite polygon boundary overlay color/width** | `DUDC V3/core_gis/satellite.py` | `generate_satellite_image()` (ImageDraw lines) |
| **Add a new administrative center or new governorate** | `DUDC V3/core_gis/jurisdictions/dakahlia.py` or `base.py` | `DAKAHLIA_CENTERS` & `DakahliaJurisdictionProvider` |
| **Change Arabic normalization (diacritics, prefixes, tatweel)** | `DUDC V3/core_gis/jurisdictions/dakahlia.py` | `normalize_arabic()` |
| **Change Modal.com cloud endpoint, API key, or timeout** | `DUDC V3/core_gis/security.py` | `CLOUD_ENDPOINT`, `generate_dudc_token()` |
| **Change server listening port or port failover range** | `DUDC V3/app_server.py` | `start_server()` & `kill_existing_on_port()` |
| **Add or modify a REST API endpoint** | `DUDC V3/server/handlers.py` | `handle_get()` or `handle_post()` |
| **Modify exported citizen folder structure or naming format** | `DUDC V3/server/handlers.py` | `handle_post()` at `/api/export-package` |
| **Modify PDF generation flags or Edge execution timeout** | `DUDC V3/server/pdf_service.py` | `export_certificate_pdf()` |
| **Change session memory storage, active session snapshot** | `DUDC V3/server/session_manager.py` | `SessionManager.update_active_session()` |
| **Modify draft saving format or base64 extraction** | `DUDC V3/server/drafts_service.py` | `save_draft()` & `ensure_base64_image()` |
| **Change in-app folder explorer backend or drive detection** | `DUDC V3/server/config.py` | `list_subdirectories()` & `get_system_drives()` |
| **Change fallback native folder picker (Tkinter / PowerShell)** | `DUDC V3/server/config.py` | `open_folder_picker()` |
| **Modify Stage 1 cards, file upload, or tolerance alerts** | `DUDC V3/js/stage1.js` | `renderParcelsList()` & `setupDropZone()` |
| **Modify Stage 2 live certificate layout, text, or DOM sync** | `DUDC V3/js/stage2.js` | `syncStage1ToStage2()` & `syncDomToActiveParcel()` |
| **Modify layout spacing slider behavior** | `DUDC V3/js/stage2.js` | `updateSpacing()` |
| **Modify DUDC watermark canvas rendering** | `DUDC V3/js/stage2.js` | `renderWatermark()` |
| **Modify Stage 3 official cloud confirmation & export trigger** | `DUDC V3/js/stage3.js` | `confirmCloudIssuance()` & `exportPackage()` |
| **Modify draft drawer UI or auto-save intervals** | `DUDC V3/js/drafts.js` | `scheduleDraftAutoSave()` & `renderDraftsList()` |
| **Modify in-app visual folder explorer UI / breadcrumbs** | `DUDC V3/js/folder_explorer.js` | `openFolderExplorerModal()` & `renderDirectoryTree()` |
| **Modify certificate A4 print CSS, margins, page breaks** | `DUDC V3/css/certificate.css` + `css/print.css` | `#certificateSheet`, `@media print` |
| **Modify application colors, glassmorphism, or dark themes** | `DUDC V3/css/tokens.css` + `css/components.css` | `:root`, `.glass-card` |
| **Modify portable runtime setup or 32-bit wheel packages** | `Setup_Portable_Runtime.bat` | `pip install` lines & `python311._pth` |
| **Modify launcher batch script or desktop shortcut creation** | `Run_DUDC_V4.bat` | Shortcut powershell command & python detection |

