---
title: Common Modification Recipes
tags: [recipes, how-to, modifications, developer-guide]
type: guide
last_updated: 2026-11-07
---

# 🍳 Common Modification Recipes (Step-by-Step Playbooks)

---

##  Recipe 1: Adding a New Field to the Certificate
**Goal:** Add a new metadata field from the survey file (e.g. "حوض رقم" or Basin Number) to the certificate table.

1. **Update Model:**
   In [`DUDC V3/core_gis/models.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/models.py), add `basin_no: str = ""` to `CadastralParcel`.
2. **Update Ingestion:**
   In [`DUDC V3/core_gis/geo.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/geo.py):
   - Add `"حوض"`, `"رقم الحوض"`, `"basin"` to `find_col()`.
   - Assign `parcel_dict["basin_no"] = clean_text_val(first_row.get(c_basin, ""))`.
3. **Update HTML Skeleton:**
   In [`DUDC V3/index.html`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/index.html), add the table cell in the certificate grid.
4. **Update Stage 2 DOM Synchronizer:**
   In [`DUDC V3/js/stage2.js`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/js/stage2.js):
   - In `syncStage1ToStage2()`, set `document.getElementById('lblBasinNo').textContent = activeParcel.basin_no || 'لا يوجد بيانات متاحة'`.
   - In `syncDomToActiveParcel()`, add bidirectional sync if editable.

---

## Recipe 2: Changing CAD Croquis Font Sizes or Colors
**Goal:** Adjust the default node numbering color or edge dimension text size.

1. Open [`DUDC V3/core_gis/croquis.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/croquis.py).
2. Locate `generate_croquis_image()`:
   - Node markers: Modify `markerfacecolor='#00E676'` and `markersize=7.5`.
   - Node labels: Modify `color='#3E2723'`, `fontsize=int(font_size_pts)`.
   - Edge length text (Inside): Modify `color='#D32F2F'` and `fontsize=int(font_size_dims)`.
   - Neighbor text (Outside): Modify `color='#0284C7'` and `fontsize=int(font_size_text)`.
3. If changing defaults in the UI, update the initial values in `DUDC V3/index.html` sliders and `DUDC V3/server/handlers.py` defaults.

---

## Recipe 3: Adding a New Governorate
**Goal:** Extend DUDC beyond Dakahlia to support Gharbia Governorate.

1. In [`DUDC V3/core_gis/jurisdictions/`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/jurisdictions/), create `gharbia.py`:
   - Subclass `BaseJurisdictionProvider`.
   - Define `GHARBIA_CENTERS = [(0, "طنطا", "Tanta"), ...]`.
   - Implement `resolve_center()` using `normalize_arabic()`.
2. In `core_gis/jurisdictions/__init__.py`, import and export `GharbiaJurisdictionProvider`.
3. Register the new provider dynamically via `set_active_provider(GharbiaJurisdictionProvider())`.

---

## Recipe 4: Adjusting A4 Margins or Print Media CSS
**Goal:** Fine-tune the PDF print layout margin.

1. Open [`DUDC V3/css/print.css`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/css/print.css).
2. Locate `@page`:
   ```css
   @page {
     size: A4 portrait;
     margin: 5mm; /* Adjust margin here */
   }
   ```
3. In [`DUDC V3/css/certificate.css`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/css/certificate.css), adjust `#certificateSheet` padding if necessary to maintain exact page containment.

