---
title: Stage 1 - Survey Ingestion (stage1.js)
tags: [frontend, stage1, upload, validation, parcel-cards]
related_files:
  - DUDC V3/js/stage1.js
---

# 💻 Stage 1 - Survey Ingestion (`stage1.js`)

File: [`DUDC V3/js/stage1.js`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/js/stage1.js)

Controls data import, legal tolerance validation, coordinate visualization, and image previews in Stage 1.

---

## 🎯 Key Responsibilities & Components

### 1. File Upload & Sample Loader
- Drag-and-drop zone (`#dropZone`) and file input (`#fileInput`).
- One-click sample test button: `⚡ تجربة العينة المرفقة (ف.xls)`.
- Server health monitor with auto-ping every 12 seconds (`checkServerHealth()`).

### 2. Multi-Parcel Selection Cards
- When an Excel file contains multiple parcels, renders selectable parcel cards.
- Displays applicant name, calculated area, and area difference badge ($\Delta$).

### 3. Legal Tolerance Badge (`is_area_valid`)
- If $|\Delta| \le 2.00\text{ m}^2$:
  Displays green badge: `✔ مطابق للتفاوت القانوني (±2.00 م²)`.
- If $|\Delta| > 2.00\text{ m}^2$:
  Displays yellow warning badge: `⚠️ غير مطابق للتفاوت القانوني (فرق X م²) - يلزم المراجعة المساحية`.

### 4. Center / District Selection (`#selDistrict`)
- Populates the 18 official Dakahlia centers.
- If the survey file name or text does not match an official center, highlights the dropdown in red and disables transitioning to Stage 2 until the user explicitly selects a valid center.

### 5. Interactive Coordinate & Segment Tables
- Coordinates Table: Node index, Lon (Easting), Lat (Northing). Includes live input fields allowing manual point adjustments.
- Segments Table: Direction, start node, end node, geodesic length, azimuth, and neighboring property owner.

### 6. Custom Image Uploaders (Stage 1 Only!)
- `btnUploadCroquis` and `btnUploadSatellite`.
- Allows surveyors to upload pre-existing AutoCAD screenshots or custom drone imagery.
- Strictly restricted to Stage 1 to prevent layout disruption in Stage 2.

