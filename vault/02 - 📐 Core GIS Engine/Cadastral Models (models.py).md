---
title: Cadastral Models (models.py)
tags: [core-gis, models, schema, dataclass]
related_files:
  - DUDC V3/core_gis/models.py
---

# 📐 Cadastral Models (`models.py`)

File: [`DUDC V3/core_gis/models.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/models.py)

Defines explicit, strongly typed dataclasses representing cadastral parcels, geometry vertices, polygon segments, and cardinal boundaries.

---

## 🏗️ Model Definitions

### 1. `Vertex`
Represents a geographic point on the WGS84 ellipsoid.
- `point_index: int` - Sequential node number (1-based index).
- `lon: float` - Longitude in decimal degrees (Easting).
- `lat: float` - Latitude in decimal degrees (Northing).
- `to_dict() -> Dict[str, Any]`

### 2. `Segment`
Represents a directed boundary edge connecting two sequential vertices.
- `from_point: int` - Starting vertex index.
- `to_point: int` - Ending vertex index.
- `direction: str` - Cardinal direction (`north`, `south`, `east`, `west`).
- `direction_name: str` - Arabic human-readable label (e.g. `الحد البحري (نقطة 1 إلى 2)`).
- `length_m: float` - Geodesic distance in meters.
- `azimuth_deg: float` - Forward azimuth in degrees ($0^\circ \dots 360^\circ$).
- `neighbor: str` - Neighboring parcel owner or property description.
- `to_dict() -> Dict[str, Any]`

### 3. `Boundaries`
Dictionary-like container for cardinal boundary descriptions:
- `north: str` - الحد البحري
- `south: str` - الحد القبلي
- `east: str` - الحد الشرقي
- `west: str` - الحد الغربي

### 4. `CadastralParcel`
The master record for a cadastral survey case.
Key attributes:
- `parcel_id: str` - Unique identifier or row FID.
- `applicant_name: str` - Citizen / applicant full name.
- `national_id: str` - 14-digit Egyptian National ID.
- `receipt_no: str` - Payment receipt number.
- `district: str` - Administrative center (e.g. `المنصورة`, `طلخا`).
- `district_id: Optional[int]` - Canonical center integer ID ($0 \dots 17$).
- `district_matched: bool` - Whether center matched official jurisdiction registry.
- `village: str` - Local village or district division.
- `address: str` - Street address or site location.
- `stated_area_m2: float` - Area stated in applicant's deed or survey sheet.
- `calculated_area_m2: float` - Precise WGS84 geodesic calculated area.
- `area_difference_m2: float` - Discrepancy $\Delta = \text{calc} - \text{stated}$.
- `perimeter_m: float` - Total perimeter length in meters.
- `transaction_type: str` - e.g. "إنشاء", "تعديل", "تعلية".
- `site_status: str` - e.g. "أرض فضاء", "مبنى قائم".
- `request_no: str` - Office request number.
- `system_officer: str` - Official issuing engineer / officer name.
- `survey_technician: str` - Survey technician name.
- `is_area_valid: bool` - `True` if $|\Delta| \le 2.00\text{ m}^2$.
- `validation_status: str` - `"PASS"` or `"MANUAL_REVISION"`.
- `security_token: Optional[str]` - Official cloud-confirmed security token.
- `font_size_pts: int`, `font_size_dims: int`, `font_size_text: int` - CAD croquis styling preferences.
- `vertices: List[Dict[str, Any]]`
- `segments: List[Dict[str, Any]]`
- `boundaries: Dict[str, str]`
- `croquis_base64: Optional[str]`
- `satellite_base64: Optional[str]`

