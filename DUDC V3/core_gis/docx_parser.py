"""
DUDC Cadastral Survey Certificate System - Word (.docx) Parser & CSV Synthesizer
===============================================================================
Extracts applicant metadata, boundaries, neighbors, and coordinates from official
Word cadastral certificates (.docx) and synthesizes a standardized survey CSV file.

Zero external dependencies: Uses Python standard library (zipfile, xml.etree.ElementTree).
100% compatible with 32-bit and 64-bit portable environments.
"""

import os
import re
import csv
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple, Optional

# XML namespaces used in WordprocessingML
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Numerals translation table
ARABIC_TO_ENG = str.maketrans('٠١٢٣٤٥٦٧٨٩،', '0123456789.')


def clean_num_val(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).translate(ARABIC_TO_ENG).replace(',', '.')
    # Strip unit words and symbols first to prevent unit numbers (like 2 in m2) from corrupting the value
    s = re.sub(r'متر\s*مربع|م\s*2|م\s*²|متر|\bم\b', '', s, flags=re.IGNORECASE)
    # Match the first floating-point or integer number in the string
    m = re.search(r'[-+]?\d*\.?\d+', s)
    return m.group(0) if m else ""


def clean_text_val(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).strip()
    return " ".join(s.split())


def extract_docx_tables(docx_file_or_bytes) -> List[List[List[str]]]:
    """
    Extracts all tables from a .docx file as 2D grids of text strings.
    Properly handles vertical cell merges (<w:vMerge>) by propagating values downward.
    """
    with zipfile.ZipFile(docx_file_or_bytes, 'r') as z:
        xml_bytes = z.read("word/document.xml")

    root = ET.fromstring(xml_bytes)
    tables = []

    for tbl in root.iter(f"{W_NS}tbl"):
        grid = []
        active_merges = {}  # col_idx -> text from restart cell

        for tr in tbl.iter(f"{W_NS}tr"):
            row = []
            col_idx = 0
            for tc in tr.iter(f"{W_NS}tc"):
                # Check for vertical merge
                tcPr = tc.find(f"{W_NS}tcPr")
                vMerge = tcPr.find(f"{W_NS}vMerge") if tcPr is not None else None

                cell_text = clean_text_val(" ".join(tc.itertext()))

                if vMerge is not None:
                    val = vMerge.get(f"{W_NS}val")
                    if val == "restart":
                        active_merges[col_idx] = cell_text
                    elif val in (None, "continue"):
                        # Inherit text from the upper merged cell
                        cell_text = active_merges.get(col_idx, cell_text)
                else:
                    active_merges.pop(col_idx, None)

                row.append(cell_text)
                col_idx += 1

            if any(cell.strip() for cell in row):
                grid.append(row)

        if grid:
            tables.append(grid)

    return tables


def parse_metadata_table(table_grid: List[List[str]]) -> Dict[str, Any]:
    """
    Extracts applicant information from key-value pairs in Table 0 or metadata table.
    """
    meta = {
        "applicant_name": "",
        "national_id": "",
        "receipt_no": "",
        "request_no": "",
        "district": "",
        "village": "",
        "address": "",
        "stated_area_m2": 0.0,
        "transaction_type": "إنشاء",
        "site_status": "أرض فضاء",
    }

    # Helper to check if a string contains any candidate key
    def match_key(text: str, *candidates) -> bool:
        norm = text.replace('ـ', '').replace('إ', 'ا').replace('أ', 'ا').replace('ة', 'ه').strip()
        for cand in candidates:
            if cand in norm:
                return True
        return False

    for row in table_grid:
        for idx, cell in enumerate(row):
            txt = clean_text_val(cell)
            if not txt:
                continue

            # Check next cell in row for value
            val = row[idx + 1] if idx + 1 < len(row) else ""
            val = clean_text_val(val)

            # If current cell has colon, e.g. "اسم مقدم الطلب: محمد أحمد"
            inline_val = ""
            if ":" in txt:
                parts = txt.split(":", 1)
                lbl = parts[0]
                inline_val = clean_text_val(parts[1])
            elif "：" in txt:
                parts = txt.split("：", 1)
                lbl = parts[0]
                inline_val = clean_text_val(parts[1])
            else:
                lbl = txt

            target_val = inline_val or val

            if match_key(lbl, "اسم مقدم الطلب", "اسم العميل", "مقدم الطلب", "اسم الطالب"):
                if target_val and not meta["applicant_name"]:
                    meta["applicant_name"] = target_val

            elif match_key(lbl, "الرقم القومي"):
                if target_val and not meta["national_id"]:
                    clean_id = clean_num_val(target_val)
                    if clean_id and clean_id != "0":
                        meta["national_id"] = clean_id

            elif match_key(lbl, "رقم ايصال السداد", "رقم الايصال", "ايصال السداد", "ايصال"):
                if target_val and not meta["receipt_no"]:
                    clean_rcp = clean_num_val(target_val)
                    if clean_rcp and clean_rcp != "0":
                        meta["receipt_no"] = clean_rcp

            elif match_key(lbl, "رقم الطلب", "طلب رقم"):
                if target_val and not meta["request_no"]:
                    meta["request_no"] = clean_num_val(target_val)

            elif match_key(lbl, "المركز"):
                if target_val and not meta["district"]:
                    meta["district"] = target_val

            elif match_key(lbl, "القرية", "القريه"):
                if target_val and not meta["village"]:
                    meta["village"] = target_val

            elif match_key(lbl, "العنوان", "الموقع"):
                if target_val and not meta["address"]:
                    meta["address"] = target_val

            elif match_key(lbl, "المساحة", "المساحه"):
                if target_val and not meta["stated_area_m2"]:
                    clean_area = clean_num_val(target_val)
                    try:
                        meta["stated_area_m2"] = float(clean_area)
                    except ValueError:
                        pass

            elif match_key(lbl, "وصف التعامل", "التعامل"):
                if target_val:
                    meta["transaction_type"] = target_val

            elif match_key(lbl, "وصف الموقع", "حالة الموقع"):
                if target_val:
                    meta["site_status"] = target_val

    return meta


def parse_coords_and_bounds_table(table_grid: List[List[str]]) -> Tuple[List[Dict[str, float]], Dict[str, str]]:
    """
    Parses boundaries descriptions and coordinate points (Easting/Lon and Northing/Lat).
    Handles both unified tables (bounds + coords) and distinct point tables.
    Returns (vertices_list, boundaries_dict).
    """
    vertices = []
    boundaries = {
        "north": "",
        "south": "",
        "east": "",
        "west": ""
    }

    # 1. Detect if there is a header row with explicit column indices
    col_x_idx = None
    col_y_idx = None
    col_length_idx = None
    col_neighbor_idx = None
    header_row_idx = None

    for r_idx, row in enumerate(table_grid[:3]):
        row_norm = [clean_text_val(c).lower() for c in row]
        for c_idx, cell in enumerate(row_norm):
            c_no_punct = cell.replace('ـ', '').replace('(', ' ').replace(')', ' ').replace('/', ' ')
            # Check for Easting / X
            if any(k in c_no_punct.split() for k in ["شرقيات", "شرق", "x", "e", "easting"]) or "خط الطول" in c_no_punct:
                col_x_idx = c_idx
                header_row_idx = r_idx
            # Check for Northing / Y
            elif any(k in c_no_punct.split() for k in ["شماليات", "y", "n", "northing"]) or "دائرة العرض" in c_no_punct or "دوائر العرض" in c_no_punct:
                col_y_idx = c_idx
                header_row_idx = r_idx
            # Check for Length
            elif "بطول" in c_no_punct or ("طول" in c_no_punct and "خط الطول" not in c_no_punct):
                col_length_idx = c_idx
            # Check for Neighbor
            elif any(k in c_no_punct for k in ["الجار", "المجاور", "الوصف"]):
                col_neighbor_idx = c_idx

        if col_x_idx is not None and col_y_idx is not None:
            break

    def detect_cardinal(text: str) -> Optional[str]:
        t = text.replace('ـ', '').replace('إ', 'ا').replace('أ', 'ا').replace('ة', 'ه').strip()
        if any(h in t for h in ["شرقيات", "شماليات", "احداثيات", "إحداثيات"]):
            return None
        if "بحري" in t or t.startswith("شمال") or "الحد الشمالي" in t:
            return "north"
        if "قبلي" in t or t.startswith("جنوب") or "الحد الجنوبي" in t:
            return "south"
        if "شرقي" in t or "الحد الشرقي" in t:
            return "east"
        if "غربي" in t or "الحد الغربي" in t:
            return "west"
        return None

    def extract_coord_num(s: str) -> Optional[float]:
        clean = clean_num_val(s)
        if not clean:
            return None
        try:
            num = float(clean)
            # In Egypt WGS84: longitude is ~20.0 to 40.0, latitude is ~20.0 to 35.0
            # Or projected coordinate (ETM / Red Belt / UTM): Easting ~100,000-900,000, Northing ~600,000-4,000,000
            if (20.0 <= num <= 40.0) or (100000.0 <= num <= 5000000.0):
                return num
        except ValueError:
            pass
        return None

    current_cardinal = None
    start_row = (header_row_idx + 1) if header_row_idx is not None else 0

    for r_idx in range(start_row, len(table_grid)):
        row = table_grid[r_idx]
        if not row or not any(c.strip() for c in row):
            continue

        row_text_full = " ".join(row)

        # Detect boundary direction
        card = detect_cardinal(row[0] if len(row) > 0 else "") or detect_cardinal(row_text_full)
        if card:
            current_cardinal = card

        # Extract neighbor description
        if current_cardinal:
            if col_neighbor_idx is not None and col_neighbor_idx < len(row):
                cand = clean_text_val(row[col_neighbor_idx])
                if cand and not boundaries[current_cardinal]:
                    boundaries[current_cardinal] = cand
            else:
                for c_idx, cell in enumerate(row):
                    cell_clean = clean_text_val(cell)
                    if not cell_clean:
                        continue
                    if detect_cardinal(cell_clean):
                        continue
                    if cell_clean.startswith("بطول") or "بطول" in cell_clean:
                        continue
                    if cell_clean in ("م", "م.", "م/", "نقطة", "رقم", "مسلسل"):
                        continue
                    if any(kw in cell_clean for kw in ("الحدود", "إحداثيات", "شرقيات", "شماليات")):
                        continue
                    if extract_coord_num(cell_clean) is not None:
                        continue
                    if re.search(r'[\u0600-\u06FFa-zA-Z]', cell_clean) and len(cell_clean) > 2:
                        if not boundaries[current_cardinal]:
                            boundaries[current_cardinal] = cell_clean
                            break

        # Coordinate extraction
        # If columns were explicitly detected via header:
        if col_x_idx is not None and col_y_idx is not None:
            if col_x_idx < len(row) and col_y_idx < len(row):
                x_val = extract_coord_num(row[col_x_idx])
                y_val = extract_coord_num(row[col_y_idx])
                if x_val is not None and y_val is not None:
                    if y_val > 1000000.0 and x_val < 1000000.0:
                        lon_val, lat_val = x_val, y_val
                    elif x_val > 1000000.0 and y_val < 1000000.0:
                        lon_val, lat_val = y_val, x_val
                    else:
                        lon_val, lat_val = x_val, y_val

                    vertices.append({
                        "point_index": len(vertices) + 1,
                        "lon": lon_val,
                        "lat": lat_val
                    })
                    continue

        # If no explicit columns detected or values were missing in those columns:
        candidate_numbers = []
        for c_idx, cell in enumerate(row):
            txt = clean_text_val(cell)
            if not txt:
                continue
            if col_length_idx is not None and c_idx == col_length_idx:
                continue
            if "بطول" in txt:
                continue
            if c_idx > 0 and "بطول" in clean_text_val(row[c_idx - 1]):
                continue
            num = extract_coord_num(cell)
            if num is not None:
                candidate_numbers.append(num)

        if len(candidate_numbers) >= 2:
            coord_x, coord_y = candidate_numbers[-2], candidate_numbers[-1]
            if coord_y > 1000000.0 and coord_x < 1000000.0:
                lon_val, lat_val = coord_x, coord_y
            elif coord_x > 1000000.0 and coord_y < 1000000.0:
                lon_val, lat_val = coord_y, coord_x
            else:
                lon_val, lat_val = coord_x, coord_y

            vertices.append({
                "point_index": len(vertices) + 1,
                "lon": lon_val,
                "lat": lat_val
            })

    return vertices, boundaries


def parse_docx_certificate(docx_path_or_bytes) -> Dict[str, Any]:
    """
    High-level parser that reads a .docx cadastral certificate,
    extracts all metadata, boundaries, and coordinates.
    """
    tables = extract_docx_tables(docx_path_or_bytes)
    if not tables:
        raise ValueError("لم يتم العثور على أي جداول داخل ملف الوورد المحدد.")

    # 1. Parse Table 0 (Metadata)
    meta = parse_metadata_table(tables[0])

    # 2. Parse Table 1 (or second table containing coordinates & boundaries)
    coords_table = tables[1] if len(tables) > 1 else tables[0]
    vertices, boundaries = parse_coords_and_bounds_table(coords_table)

    # If coordinates were not found in table 1, scan remaining tables
    if len(vertices) < 3 and len(tables) > 2:
        for t in tables[2:]:
            v, b = parse_coords_and_bounds_table(t)
            if len(v) >= 3:
                vertices = v
                for k, val in b.items():
                    if val and not boundaries.get(k):
                        boundaries[k] = val
                break

    # If boundaries were found in meta table or text
    if not any(boundaries.values()):
        for t in tables:
            _, b = parse_coords_and_bounds_table(t)
            for k, val in b.items():
                if val and not boundaries.get(k):
                    boundaries[k] = val

    return {
        "metadata": meta,
        "vertices": vertices,
        "boundaries": boundaries
    }


def docx_to_survey_csv(docx_path_or_bytes, output_csv_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses a .docx cadastral certificate and writes a standardized, fully-compatible
    survey CSV file with UTF-8 BOM encoding for seamless Excel / DUDC ingestion.

    Returns (output_csv_path, parsed_data_dict).
    """
    parsed = parse_docx_certificate(docx_path_or_bytes)
    meta = parsed["metadata"]
    vertices = parsed["vertices"]
    bounds = parsed["boundaries"]

    if len(vertices) < 3:
        raise ValueError(
            f"تم العثور على {len(vertices)} نقطة فقط في ملف الوورد. "
            "يتطلب الرفع المساحي 3 نقاط على الأقل لتكوين مضلع هندسي صحيح."
        )

    headers = [
        "ORIG_FID",
        "اسم مقدم الطلب",
        "الرقم القومي",
        "رقم ايصال السداد",
        "المركز",
        "القرية",
        "العنوان",
        "المساحة م2",
        "وصف التعامل",
        "وصف الموقع",
        "رقم الطلب",
        "الحد_البحري",
        "الحد_القبلي",
        "الحد_الشرقي",
        "الحد_الغربي",
        "POINT_X",
        "POINT_Y"
    ]

    os.makedirs(os.path.dirname(os.path.abspath(output_csv_path)), exist_ok=True)

    with open(output_csv_path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        applicant = meta.get("applicant_name") or "مواطن"
        nid = meta.get("national_id") or ""
        rcp = meta.get("receipt_no") or ""
        dist = meta.get("district") or ""
        vill = meta.get("village") or ""
        addr = meta.get("address") or ""
        area = meta.get("stated_area_m2") or 0.0
        trans = meta.get("transaction_type") or "إنشاء"
        site = meta.get("site_status") or "أرض فضاء"
        req_no = meta.get("request_no") or ""

        b_north = bounds.get("north", "")
        b_south = bounds.get("south", "")
        b_east = bounds.get("east", "")
        b_west = bounds.get("west", "")

        for v in vertices:
            row = [
                1,              # ORIG_FID
                applicant,
                nid,
                rcp,
                dist,
                vill,
                addr,
                area,
                trans,
                site,
                req_no,
                b_north,
                b_south,
                b_east,
                b_west,
                f"{v['lon']:.8f}",
                f"{v['lat']:.8f}"
            ]
            writer.writerow(row)

    return output_csv_path, parsed
