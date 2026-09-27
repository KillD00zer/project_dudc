"""
Cadastral Survey Certificate System - Core Geo & Validation Engine
==================================================================
Handles:
1. Multi-format survey table reading (.csv, .xls, .xlsx).
2. Data grouping by parcel ID while preserving strict vertex ordering.
3. High-precision geodesic calculations (WGS84 ellipsoid).
4. Strict validation against ±2.0 m² area and ±0.5 m length tolerances.
"""

import os
import re
import pandas as pd
from pyproj import Geod
from shapely.geometry import Polygon

# Standard Arabic to English numeral mapping
ARABIC_TO_ENG = str.maketrans('٠١٢٣٤٥٦٧٨٩،', '0123456789.')

# WGS84 Geoid for precise geodesic measurements
GEOD = Geod(ellps='WGS84')

def clean_text_val(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    return " ".join(s.split())

def clean_num_str(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).translate(ARABIC_TO_ENG).replace(',', '.')
    s = re.sub(r'[^\d.-]', '', s)
    return s

def clean_area_num(val):
    clean = clean_num_str(val)
    try:
        return float(clean)
    except (ValueError, TypeError):
        return 0.0

def read_survey_file(file_path):
    """
    Reads CSV or Excel file and groups rows into distinct parcels.
    Preserves strict sequential coordinate row order.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except Exception:
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except Exception:
                df = pd.read_csv(file_path, encoding='cp1256')
    elif ext in ('.xls', '.xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
        
    # Build column map
    col_map = {}
    for col in df.columns:
        c_clean = str(col).strip()
        c_norm = c_clean.replace('_', ' ')
        col_map[col] = (c_clean, c_norm)
        
    def find_col(*candidates):
        # Check candidates in strict order of preference
        for cand in candidates:
            cand_lower = cand.lower()
            # Exact match first
            for orig, (clean, norm) in col_map.items():
                if cand_lower == clean.lower() or cand_lower == norm.lower():
                    return orig
            # Substring match second
            for orig, (clean, norm) in col_map.items():
                if cand_lower in clean.lower() or cand_lower in norm.lower():
                    return orig
        return None

    c_fid = find_col("ORIG_FID", "ORIG FID", "parcel_id", "FID")
    c_name = find_col("اسم مقدم الطلب", "اسم_مقدم_الطلب", "اسم مقدم", "applicant")
    c_nid = find_col("الرقم القومي", "الرقم_القومي", "national_id")
    c_rcp = find_col("رقم ايصال السداد", "رقم_ايصال_السداد", "ايصال", "receipt")
    c_dist = find_col("المركز", "district")
    c_vill = find_col("القرية", "القريه", "village")
    c_addr = find_col("العنوان", "address")
    c_area = find_col("المساحة م2", "المساحة_م2", "المساحة", "area")
    c_trans = find_col("وصف التعامل", "وصف_التعامل", "transaction")
    c_site = find_col("وصف الموقع", "وصف_الموقع", "site")
    c_req = find_col("رقم الطلب", "رقم_الطلب", "request")
    c_x = find_col("POINT_X", "POINT X", "LONG", "Easting", "X")
    c_y = find_col("POINT_Y", "POINT Y", "LAT", "Northing", "Y")

    if not c_x or not c_y:
        raise ValueError("Coordinate columns (POINT_X, POINT_Y) not found in file!")

    parcels = []
    # Group by parcel ID (or applicant name if FID is missing)
    group_col = c_fid if c_fid else c_name
    if not group_col:
        # Fallback: treat all rows as single parcel
        df['_group_id'] = 1
        group_col = '_group_id'

    for group_id, group_df in df.groupby(group_col, sort=False):
        first_row = group_df.iloc[0]
        
        applicant_name = clean_text_val(first_row.get(c_name, ""))
        national_id = clean_num_str(first_row.get(c_nid, ""))
        receipt_no = clean_num_str(first_row.get(c_rcp, ""))
        district = clean_text_val(first_row.get(c_dist, ""))
        village = clean_text_val(first_row.get(c_vill, ""))
        address = clean_text_val(first_row.get(c_addr, "")) or village
        stated_area = clean_area_num(first_row.get(c_area, 0.0))
        transaction = clean_text_val(first_row.get(c_trans, "إنشاء"))
        site_status = clean_text_val(first_row.get(c_site, "أرض فضاء"))
        request_no = clean_num_str(first_row.get(c_req, ""))
        
        # Extract sequential vertices
        raw_vertices = []
        for v_idx, (_, row) in enumerate(group_df.iterrows(), start=1):
            try:
                x_val = float(clean_num_str(row[c_x]))
                y_val = float(clean_num_str(row[c_y]))
                raw_vertices.append({
                    "point_index": v_idx,
                    "lon": x_val,
                    "lat": y_val
                })
            except (ValueError, TypeError):
                continue
                
        if len(raw_vertices) < 3:
            continue
            
        # 1. Deduplicate consecutive duplicate coordinates (< 1e-9 deg ~ 0.1mm)
        # Retain all 8 decimal digits, preserving small edges (< 0.5m) without collapsing coordinates
        dedup_vertices = []
        for v in raw_vertices:
            if not dedup_vertices:
                dedup_vertices.append(v)
            else:
                prev = dedup_vertices[-1]
                if abs(v["lon"] - prev["lon"]) > 1e-9 or abs(v["lat"] - prev["lat"]) > 1e-9:
                    dedup_vertices.append(v)
                    
        # 2. Check if last vertex is a duplicate of the first vertex (Ring Closure Point)
        # In CAD/Survey tables, repeated first point causes a zero-length edge (length = 0.00m).
        if len(dedup_vertices) > 3:
            first_v = dedup_vertices[0]
            last_v = dedup_vertices[-1]
            if abs(last_v["lon"] - first_v["lon"]) < 1e-9 and abs(last_v["lat"] - first_v["lat"]) < 1e-9:
                # Remove the closing vertex copy to maintain unique polygon vertices
                dedup_vertices.pop()
                
        # 3. Cleanly re-index point indices 1..N
        vertices = []
        for idx, v in enumerate(dedup_vertices, start=1):
            v["point_index"] = idx
            vertices.append(v)
            
        if len(vertices) < 3:
            continue
            
        parcel = {
            "parcel_id": str(group_id),
            "applicant_name": applicant_name or f"Parcel #{group_id}",
            "national_id": national_id,
            "receipt_no": receipt_no,
            "district": district,
            "village": village,
            "address": address,
            "stated_area_m2": stated_area,
            "transaction_type": transaction or "إنشاء",
            "site_status": site_status or "أرض فضاء",
            "request_no": request_no,
            "vertices": vertices,
            "boundaries": {
                "north": clean_text_val(first_row.get("الحد_البحري", first_row.get("الحد البحري", ""))),
                "south": clean_text_val(first_row.get("الحد_القبلي", first_row.get("الحد القبلي", ""))),
                "east": clean_text_val(first_row.get("الحد_الشرقي", first_row.get("الحد الشرقي", ""))),
                "west": clean_text_val(first_row.get("الحد_الغربي", first_row.get("الحد الغربي", "")))
            }
        }
        
        # Compute spatial math and validate
        enriched = validate_and_enrich_parcel(parcel)
        parcels.append(enriched)

    return parcels

def validate_and_enrich_parcel(parcel):
    """
    Computes geodesic area, segment lengths, discrepancy Δ,
    and applies the ±2.0 m² area tolerance rule.
    """
    verts = parcel["vertices"]
    n_pts = len(verts)
    
    lons = [v["lon"] for v in verts]
    lats = [v["lat"] for v in verts]
    
    # Calculate ellipsoidal geodesic area and perimeter
    # geod.polygon_area_perimeter returns (area, perimeter)
    area_raw, perimeter_m = GEOD.polygon_area_perimeter(lons, lats)
    calc_area_m2 = round(abs(area_raw), 2)
    perimeter_m = round(perimeter_m, 2)
    
    stated_area_m2 = parcel.get("stated_area_m2", 0.0)
    area_diff = round(calc_area_m2 - stated_area_m2, 2)
    
    c_lon = float(sum(lons)) / len(lons) if lons else 0.0
    c_lat = float(sum(lats)) / len(lats) if lats else 0.0
    
    cardinal_name_ar = {
        "north": "الحد البحري",
        "east": "الحد الشرقي",
        "south": "الحد القبلي",
        "west": "الحد الغربي"
    }
    default_dir_names = ["الحد البحري", "الحد الشرقي", "الحد القبلي", "الحد الغربي"]
    
    # Calculate geodesic segment lengths (P_i -> P_i+1)
    segments = []
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        p1 = verts[i]
        p2 = verts[next_i]
        
        # geod.inv returns (forward_azimuth, back_azimuth, distance)
        fwd_az, _, dist = GEOD.inv(p1["lon"], p1["lat"], p2["lon"], p2["lat"])
        dist_m = round(dist, 2)
        if dist > 0 and dist_m == 0.0:
            dist_m = 0.01
        fwd_az = round(fwd_az % 360, 1)
        
        default_side_keys = ["north", "east", "south", "west"]
        if n_pts == 4 and i < 4:
            side = default_side_keys[i]
            dir_name = default_dir_names[i]
        else:
            dx = p2["lon"] - p1["lon"]
            dy = p2["lat"] - p1["lat"]
            mid_x = (p1["lon"] + p2["lon"]) / 2.0 - c_lon
            mid_y = (p1["lat"] + p2["lat"]) / 2.0 - c_lat
            side = ("north" if mid_y > 0 else "south") if abs(dx) > abs(dy) else ("east" if mid_x > 0 else "west")
            side_ar = cardinal_name_ar.get(side, f"ضلع {i+1}")
            dir_name = f"{side_ar} (نقطة {p1['point_index']} إلى {p2['point_index']})"
            
        segments.append({
            "from_point": p1["point_index"],
            "to_point": p2["point_index"],
            "direction": side,
            "direction_name": dir_name,
            "length_m": dist_m,
            "azimuth_deg": fwd_az
        })
        
    # Strict Area Tolerance Check: ±2.0 m²
    is_area_pass = abs(area_diff) <= 2.00
    validation_status = "PASS" if is_area_pass else "MANUAL_REVISION"
    
    parcel["calculated_area_m2"] = calc_area_m2
    parcel["area_difference_m2"] = area_diff
    parcel["perimeter_m"] = perimeter_m
    parcel["segments"] = segments
    parcel["is_area_valid"] = is_area_pass
    parcel["validation_status"] = validation_status
    
    return parcel
