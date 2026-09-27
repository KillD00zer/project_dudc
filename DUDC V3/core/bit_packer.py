"""
DUDC Compact Bit-Packer & Unpacker (Two-Point Architecture - Option 1)
======================================================================
Packs cadastral certificate attributes into exactly 210 bits (36 Base58 characters):
- 84 bits  : Exact Arabic Citizen Name (14 characters x 6 bits as-is via char_mapper)
- 21 bits  : P1 Longitude E (30/31 prefix + 6 decimal digits)
- 21 bits  : P1 Latitude N (30/31 prefix + 6 decimal digits)
- 16 bits  : P2 Delta Longitude (+-32,768 micro-degrees = +-3.1 km from P1)
- 16 bits  : P2 Delta Latitude (+-32,768 micro-degrees = +-3.6 km from P1)
- 21 bits  : Payment Receipt (20 bits number + 1 bit dual consecutive flag)
- 5 bits   : Center/District ID (0-17)
- 14 bits  : Date (Day 5 bits + Month 4 bits + Year 5 bits)
- 12 bits  : Anti-Tamper Security Tag (HMAC-SHA256 derived)
Total: 210 bits (fits into 36 Base58 characters in 6 blocks of 6)
"""

import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple

from core.char_mapper import encode_exact_arabic, decode_exact_arabic

DELTA_OFFSET = 32768  # 16-bit offset for signed delta (-32768 to +32767)

# ---------------------------------------------------------------------------
# Coordinate Packing (P1 absolute 21 bits, P2 delta 16 bits)
# ---------------------------------------------------------------------------
def pack_coord_21bits(coord_val: float) -> int:
    """Pack coordinate into 21 bits (1 bit prefix 30/31 + 20 bits for 6 decimals)."""
    val = float(coord_val)
    int_prefix = int(val)
    if int_prefix == 30:
        prefix_bit = 0
    elif int_prefix == 31:
        prefix_bit = 1
    else:
        prefix_bit = 1 if val >= 31.0 else 0
        
    decimals = int(round((abs(val) - int_prefix) * 1_000_000))
    decimals = max(0, min(999_999, decimals))
    return ((prefix_bit & 0x01) << 20) | (decimals & 0xFFFFF)

def unpack_coord_21bits(packed: int) -> float:
    """Unpack 21 bits to floating coordinate with 6 decimals."""
    prefix_bit = (packed >> 20) & 0x01
    decimals = packed & 0xFFFFF
    int_prefix = 31 if prefix_bit == 1 else 30
    return round(int_prefix + (decimals / 1_000_000.0), 6)

def pack_delta_16bits(p1_val: float, p2_val: float) -> int:
    """Pack P2 as 16-bit signed micro-degree delta from P1."""
    if not p2_val or abs(float(p2_val)) < 1.0:
        return DELTA_OFFSET  # delta = 0
    delta_micro = int(round((float(p2_val) - float(p1_val)) * 1_000_000))
    val = delta_micro + DELTA_OFFSET
    val = max(0, min(65535, val))
    return val & 0xFFFF

def unpack_delta_16bits(p1_val: float, packed: int) -> float:
    """Unpack 16-bit delta to recover P2 coordinate with 6 decimals."""
    delta_micro = (packed & 0xFFFF) - DELTA_OFFSET
    return round(p1_val + (delta_micro / 1_000_000.0), 6)

# ---------------------------------------------------------------------------
# Receipt Packing (21 bits: 20 bits number + 1 bit dual consecutive flag)
# ---------------------------------------------------------------------------
def pack_receipt_21bits(receipt_1: int, receipt_2: int = 0) -> int:
    """Pack receipt into 21 bits (up to 999,999 + dual flag)."""
    r1 = max(0, min(999_999, int(receipt_1)))
    is_dual = 1 if (receipt_2 and int(receipt_2) > 0) else 0
    return ((is_dual & 0x01) << 20) | (r1 & 0xFFFFF)

def unpack_receipt_21bits(packed: int) -> Tuple[int, int]:
    """Unpack 21 bits to (receipt_1, receipt_2)."""
    is_dual = (packed >> 20) & 0x01
    r1 = packed & 0xFFFFF
    r2 = (r1 + 1) if is_dual else 0
    return r1, r2

# ---------------------------------------------------------------------------
# Date Packing (14 bits: Day 5 bits, Month 4 bits, Year 5 bits)
# ---------------------------------------------------------------------------
def pack_date_14bits(date_val: Any = None) -> int:
    """Pack date into 14 bits (Day 1-31, Month 1-12, Year offset 0-31 from 2020)."""
    if isinstance(date_val, str):
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
            try:
                dt = datetime.strptime(date_val.strip(), fmt)
                break
            except ValueError:
                dt = datetime.now()
    elif isinstance(date_val, datetime):
        dt = date_val
    else:
        dt = datetime.now()
        
    day = max(1, min(31, dt.day))
    month = max(1, min(12, dt.month))
    year_offset = max(0, min(31, dt.year - 2020))
    return ((day & 0x1F) << 9) | ((month & 0x0F) << 5) | (year_offset & 0x1F)

def unpack_date_14bits(packed: int) -> str:
    """Unpack 14 bits to formatted date string YYYY-MM-DD."""
    day = (packed >> 9) & 0x1F
    month = (packed >> 5) & 0x0F
    year_offset = packed & 0x1F
    year = 2020 + year_offset
    day = max(1, min(31, day))
    month = max(1, min(12, month))
    return f'{year:04d}-{month:02d}-{day:02d}'

# ---------------------------------------------------------------------------
# Anti-Tamper Security Tag (12 bits HMAC)
# ---------------------------------------------------------------------------
INTERNAL_TAG_SALT = b"DUDC_DAKAHLIA_GEOSPATIAL_SECURITY_SALT_v3_TWO_POINTS"

def compute_tamper_tag_12bits(payload_198bits: int) -> int:
    """Compute 12-bit truncated HMAC from 198-bit payload."""
    payload_bytes = payload_198bits.to_bytes(25, byteorder='big')
    h = hmac.new(INTERNAL_TAG_SALT, payload_bytes, hashlib.sha256).digest()
    tag_int = int.from_bytes(h[:2], byteorder='big') & 0xFFF  # 12 bits
    return tag_int

# ---------------------------------------------------------------------------
# Master 210-Bit Assembler & Disassembler (Two-Point Edition)
# ---------------------------------------------------------------------------
def pack_all_210bits(name: str, lon: float, lat: float,
                     lon_2: float = 0.0, lat_2: float = 0.0,
                     receipt_1: int = 0, receipt_2: int = 0,
                     center_id: int = 0, date_val: Any = None) -> int:
    """
    Assemble all certificate attributes into a single 210-bit integer.
    Payload (198 bits):
      [84 Name] [21 Lon1] [21 Lat1] [16 dLon2] [16 dLat2] [21 Receipt] [5 Center] [14 Date]
    Tag (12 bits):
      [12 HMAC Tag]
    Total: 210 bits
    """
    name_bits = encode_exact_arabic(name, max_chars=14)      # 84 bits
    lon_bits = pack_coord_21bits(lon)                        # 21 bits
    lat_bits = pack_coord_21bits(lat)                        # 21 bits
    dlon_bits = pack_delta_16bits(lon, lon_2)                # 16 bits
    dlat_bits = pack_delta_16bits(lat, lat_2)                # 16 bits
    receipt_bits = pack_receipt_21bits(receipt_1, receipt_2) # 21 bits
    center_bits = max(0, min(31, int(center_id)))            # 5 bits
    date_bits = pack_date_14bits(date_val)                   # 14 bits
    
    # Pack 198-bit payload
    payload_198 = 0
    payload_198 = (payload_198 << 84) | name_bits
    payload_198 = (payload_198 << 21) | lon_bits
    payload_198 = (payload_198 << 21) | lat_bits
    payload_198 = (payload_198 << 16) | dlon_bits
    payload_198 = (payload_198 << 16) | dlat_bits
    payload_198 = (payload_198 << 21) | receipt_bits
    payload_198 = (payload_198 << 5)  | center_bits
    payload_198 = (payload_198 << 14) | date_bits
    
    # Compute 12-bit tag
    tag_12 = compute_tamper_tag_12bits(payload_198)
    
    # Final 210-bit integer
    full_210 = (payload_198 << 12) | tag_12
    return full_210

def unpack_all_210bits(full_210: int) -> Tuple[bool, Dict[str, Any]]:
    """Unpack 210-bit integer and verify anti-tamper tag. Returns (is_valid, data_dict)."""
    tag_12 = full_210 & 0xFFF
    payload_198 = full_210 >> 12
    
    expected_tag = compute_tamper_tag_12bits(payload_198)
    is_valid = (tag_12 == expected_tag)
    
    temp = payload_198
    date_bits = temp & 0x3FFF; temp >>= 14
    center_bits = temp & 0x1F; temp >>= 5
    receipt_bits = temp & 0x1FFFFF; temp >>= 21
    dlat_bits = temp & 0xFFFF; temp >>= 16
    dlon_bits = temp & 0xFFFF; temp >>= 16
    lat_bits = temp & 0x1FFFFF; temp >>= 21
    lon_bits = temp & 0x1FFFFF; temp >>= 21
    name_bits = temp & ((1 << 84) - 1)
    
    name = decode_exact_arabic(name_bits, max_chars=14)
    lon_1 = unpack_coord_21bits(lon_bits)
    lat_1 = unpack_coord_21bits(lat_bits)
    lon_2 = unpack_delta_16bits(lon_1, dlon_bits)
    lat_2 = unpack_delta_16bits(lat_1, dlat_bits)
    has_p2 = (dlon_bits != DELTA_OFFSET or dlat_bits != DELTA_OFFSET)
    r1, r2 = unpack_receipt_21bits(receipt_bits)
    issue_date = unpack_date_14bits(date_bits)
    
    data = {
        'name': name,
        'lon_1': lon_1,
        'lat_1': lat_1,
        'lon_2': lon_2,
        'lat_2': lat_2,
        'has_p2': has_p2,
        'receipt_1': r1,
        'receipt_2': r2,
        'center_id': center_bits,
        'issue_date': issue_date,
        'is_valid': is_valid
    }
    return is_valid, data
