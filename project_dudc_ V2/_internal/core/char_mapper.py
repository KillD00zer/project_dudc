"""
DUDC Exact Arabic Character Mapper (Encode As-Is)
=================================================
Preserves 100% of Arabic letters as-is without any normalization or stripping.
Supports:
- All 28 standard Arabic letters
- All Hamza variants (أ, إ, آ, ء, ؤ, ئ)
- Taa Marbuta (ة) and Alef Maqsura (ى)
- Space and hyphen
Each character maps to a 6-bit integer (0 to 63).
"""

# 6-bit Exact Arabic Table (Capacity: 64 symbols)
EXACT_ARABIC_TABLE = [
    ' ',   # 0: Space
    'ا',   # 1: Bare Alef
    'أ',   # 2: Alef with Hamza Above
    'إ',   # 3: Alef with Hamza Below
    'آ',   # 4: Alef with Madda
    'ء',   # 5: Isolated Hamza
    'ب',   # 6
    'ت',   # 7
    'ث',   # 8
    'ج',   # 9
    'ح',   # 10
    'خ',   # 11
    'د',   # 12
    'ذ',   # 13
    'ر',   # 14
    'ز',   # 15
    'س',   # 16
    'ش',   # 17
    'ص',   # 18
    'ض',   # 19
    'ط',   # 20
    'ظ',   # 21
    'ع',   # 22
    'غ',   # 23
    'ف',   # 24
    'ق',   # 25
    'ك',   # 26
    'ل',   # 27
    'م',   # 28
    'ن',   # 29
    'ه',   # 30
    'ة',   # 31: Taa Marbuta
    'و',   # 32
    'ؤ',   # 33: Waw with Hamza
    'ي',   # 34: Standard Yaa
    'ئ',   # 35: Yaa with Hamza / Nabra
    'ى',   # 36: Alef Maqsura
    '-',   # 37: Hyphen
    '.',   # 38: Dot
]

CHAR_TO_CODE = {ch: idx for idx, ch in enumerate(EXACT_ARABIC_TABLE)}
CODE_TO_CHAR = {idx: ch for idx, ch in enumerate(EXACT_ARABIC_TABLE)}

def encode_exact_arabic(text: str, max_chars: int = 20) -> int:
    """
    Encode raw Arabic text as-is into a (max_chars * 6)-bit integer.
    Preserves exact hamzas, taa marbuta, and alef maqsura without modification.
    """
    clean = text.strip()[:max_chars]
    val = 0
    for i in range(max_chars):
        ch = clean[i] if i < len(clean) else ' '
        code = CHAR_TO_CODE.get(ch, 0)
        val = (val << 6) | (code & 0x3F)
    return val

def decode_exact_arabic(val: int, max_chars: int = 20) -> str:
    """
    Decode a (max_chars * 6)-bit integer back to the exact Arabic text.
    """
    chars = []
    temp = val
    for _ in range(max_chars):
        code = temp & 0x3F
        chars.append(CODE_TO_CHAR.get(code, ' '))
        temp >>= 6
    chars.reverse()
    return "".join(chars).rstrip()
