---
title: Core GIS Engine Overview
tags: [core-gis, package, architecture, api]
related_files:
  - DUDC V3/core_gis/__init__.py
---

# 📐 Core GIS Engine Overview (`core_gis`)

The `core_gis` package is a self-contained, standalone GIS and geodesic processing library. It has zero coupling to HTTP request handlers, HTML templates, or frontend logic.

It can be imported directly into Python automation scripts, ArcGIS Pro geoprocessing toolboxes, QGIS plugins, or headless CLI utilities.

---

## 📦 Package Structure

```text
DUDC V3/core_gis/
├── __init__.py                # Public API facade & convenient re-exports
├── models.py                  # Dataclasses: CadastralParcel, Vertex, Segment, Boundaries
├── geo.py                     # WGS84 Geodesic area, perimeter, and file readers
├── croquis.py                 # Thread-safe OO Matplotlib CAD sketch generator
├── satellite.py               # Google tile fetcher, stitcher & polygon overlay
├── security.py                # Modal.com cloud token client
└── jurisdictions/             # Multi-center administrative providers
    ├── __init__.py
    ├── base.py                # Abstract BaseJurisdictionProvider
    ├── dakahlia.py            # 18 Dakahlia Centers & Arabic normalizer
    └── resolver.py            # Global active provider registry
```

---

## 🚀 External Reusability Pattern

To use `core_gis` inside an independent GIS script:

```python
import sys
sys.path.append(r"d:\Work\certi_processing_tools\project_dudc\DUDC V3")

import core_gis

# 1. Parse survey file & validate
parcels = core_gis.read_survey_file("sample_survey.xls")
p = parcels[0]
print(f"Parcel: {p['applicant_name']} | Area: {p['calculated_area_m2']} m² | Pass: {p['is_area_valid']}")

# 2. Render CAD Croquis image
core_gis.generate_croquis_image(p, "output_croquis.png", font_size_pts=14)

# 3. Fetch Satellite Map
core_gis.generate_satellite_image(p, "output_satellite.jpg")

# 4. Resolve administrative center
matched, cid, canon = core_gis.resolve_center("مركز المنصوره")
print(f"Canonical Center: {canon} (ID: {cid})")
```

