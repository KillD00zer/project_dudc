"""
Dakahlia Governorate Jurisdiction Provider
==========================================
Dakahlia Utility Data Center (DUDC) official 18 administrative centers
and morphological Arabic text normalization.
"""

import re
from typing import Tuple, List, Optional
from .base import BaseJurisdictionProvider


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


NORMALIZED_CENTERS = [
    (cid, ar_name, normalize_arabic(ar_name))
    for cid, ar_name, _ in DAKAHLIA_CENTERS
]


class DakahliaJurisdictionProvider(BaseJurisdictionProvider):
    @property
    def governorate_name(self) -> str:
        return "الدقهلية"

    def resolve_center(self, raw_name: str) -> Tuple[bool, int, str]:
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

        return False, -1, raw_str

    def get_center_name(self, center_id: int) -> str:
        return CENTER_ID_TO_NAME.get(center_id, f"مركز غير معرف ({center_id})")

    def list_all_centers(self) -> List[Tuple[int, str]]:
        return [(cid, ar) for cid, ar, _ in DAKAHLIA_CENTERS]
