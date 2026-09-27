import re
from typing import Tuple, Optional

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

def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for resilient phonetic and morphological comparison:
    - Strips tashkeel (diacritics) & tatweel
    - Unifies Alef variants (أ, إ, آ, ٱ -> ا)
    - Unifies Taa Marbuta & Haa (ة -> ه)
    - Unifies Alef Maqsura & Yaa (ى -> ي)
    - Strips administrative prefixes (مركز, مدينة, حي, قسم, بندر)
    """
    if not text:
        return ""
    # Strip diacritics
    text = re.sub(r'[\u064B-\u065F\u0670]', '', str(text))
    # Strip tatweel
    text = text.replace('ـ', '')
    # Normalize Alef forms
    text = re.sub(r'[أإآٱ]', 'ا', text)
    # Normalize Taa Marbuta
    text = text.replace('ة', 'ه')
    # Normalize Alef Maqsura
    text = text.replace('ى', 'ي')
    
    cleaned = text.strip()
    # Strip common administrative prefixes
    prefixes = ['مركز ', 'مدينة ', 'حي ', 'قسم ', 'بندر ']
    for p in prefixes:
        if cleaned.startswith(p):
            cleaned = cleaned[len(p):].strip()
            
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# Precompute normalized names for fast and accurate resolution
NORMALIZED_CENTERS = []
for cid, ar_name, en_name in DAKAHLIA_CENTERS:
    NORMALIZED_CENTERS.append((cid, ar_name, normalize_arabic(ar_name)))

def resolve_center(raw_name: str) -> Tuple[bool, int, str]:
    """
    Strict and resilient resolution of any raw center input against Dakahlia's official 18 centers.
    
    Returns:
        (is_matched: bool, center_id: int, canonical_arabic_name: str)
        - If matched: (True, 0..17, official_name)
        - If NOT matched: (False, -1, raw_name)
    """
    if not raw_name:
        return False, -1, ""
        
    raw_str = str(raw_name).strip()
    if not raw_str:
        return False, -1, ""
        
    # 1. Exact canonical name match
    if raw_str in CENTER_NAME_TO_ID:
        cid = CENTER_NAME_TO_ID[raw_str]
        return True, cid, CENTER_ID_TO_NAME[cid]
        
    # 2. Normalized full match
    norm_input = normalize_arabic(raw_str)
    if not norm_input:
        return False, -1, raw_str
        
    for cid, ar_name, norm_official in NORMALIZED_CENTERS:
        if norm_input == norm_official:
            return True, cid, ar_name
            
    # 3. Substring / Containment match (e.g. "حي غرب المنصورة" -> "المنصورة", "بندر نبروة" -> "نبروه")
    for cid, ar_name, norm_official in NORMALIZED_CENTERS:
        if norm_official in norm_input or norm_input in norm_official:
            return True, cid, ar_name
            
    # No match found - do NOT fallback to default 0
    return False, -1, raw_str

def get_center_name(center_id: int) -> str:
    """Return official Arabic center name for a given center ID (0-17)."""
    return CENTER_ID_TO_NAME.get(center_id, f"مركز غير معرف ({center_id})")

def get_center_id(name: str) -> int:
    """Backward-compatible resolver returning center ID (defaults to 0 if unmatched)."""
    is_matched, cid, _ = resolve_center(name)
    return cid if is_matched else 0

def list_all_centers():
    """Return list of all 18 official centers for UI dropdowns: [(0, 'المنصورة'), ...]"""
    return [(cid, ar) for cid, ar, _ in DAKAHLIA_CENTERS]
