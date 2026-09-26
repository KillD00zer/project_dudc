"""
DUDC Dakahlia Centers and Districts Registry
============================================
Official list of 18 administrative centers and cities in Dakahlia Governorate.
Mapped to 5-bit integer IDs (0 to 31 capacity).
"""

DAKAHLIA_CENTERS = [
    (0, "المنصورة", "Mansoura"),
    (1, "طلخا", "Talkha"),
    (2, "ميت غمر", "Mit Ghamr"),
    (3, "دكرنس", "Dikirnis"),
    (4, "السنبلاوين", "Simbillawein"),
    (5, "بلقاس", "Bilqas"),
    (6, "شربين", "Sherbin"),
    (7, "المنزلة", "Manzala"),
    (8, "منية النصر", "Minyat El Nasr"),
    (9, "أجا", "Aga"),
    (10, "نبروه", "Nabaroh"),
    (11, "تمي الأمديد", "Temay El Amdeed"),
    (12, "الجمالية", "Gamaliya"),
    (13, "الكردي", "El Kurdi"),
    (14, "المطرية", "Matariya"),
    (15, "ميت سلسيل", "Mit Salsil"),
    (16, "بني عبيد", "Bani Ubaid"),
    (17, "جمصة", "Gamasa"),
]

CENTER_ID_TO_NAME = {cid: ar for cid, ar, _ in DAKAHLIA_CENTERS}
CENTER_NAME_TO_ID = {ar: cid for cid, ar, _ in DAKAHLIA_CENTERS}

def get_center_name(center_id: int) -> str:
    """Return official Arabic center name for a given center ID (0-17)."""
    return CENTER_ID_TO_NAME.get(center_id, f"مركز غير معرف ({center_id})")

def get_center_id(name: str) -> int:
    """Resolve center name to ID with fuzzy/prefix fallback."""
    clean = name.strip()
    if clean in CENTER_NAME_TO_ID:
        return CENTER_NAME_TO_ID[clean]
    
    # Strip prefix 'مركز ' or 'مدينة ' or 'حي '
    simplified = clean.replace("مركز ", "").replace("مدينة ", "").replace("حي ", "").strip()
    for ar, cid in CENTER_NAME_TO_ID.items():
        if simplified in ar or ar in simplified:
            return cid
    return 0  # Default to Mansoura

def list_all_centers():
    """Return list of all official centers for UI dropdowns."""
    return [(cid, ar) for cid, ar, _ in DAKAHLIA_CENTERS]
