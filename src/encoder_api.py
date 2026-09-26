"""
DUDC Certificate Encoder & Verifier API (Two-Point Architecture - Option 1)
===========================================================================
Unified programmatic API exposing:
1. generate_dudc_token: Generates encrypted 36-character security tokens holding P1 AND P2
2. verify_dudc_token: Validates, decrypts, and unpacks both points with GIS copy strings
"""

from typing import Dict, Any, Union
from core.bit_packer import pack_all_210bits, unpack_all_210bits
from core.crypto_engine import encrypt_210bits, decrypt_210bits, verify_manager_password
from core.base58_codec import b58encode_int, b58decode_int, format_token, parse_token
from core.centers import get_center_id, get_center_name

def generate_dudc_token(
    name: str,
    lon: float,
    lat: float,
    lon_2: float = 0.0,
    lat_2: float = 0.0,
    receipt_1: Union[int, str] = 0,
    receipt_2: Union[int, str] = 0,
    center: Union[int, str] = 0,
    date_val: Any = None
) -> str:
    """
    Generate an official DUDC Cadastral Security Token with Two Coordinate Points.
    """
    if isinstance(center, str):
        cid = get_center_id(center)
    else:
        cid = int(center)
        
    r1 = int(receipt_1) if receipt_1 else 0
    r2 = int(receipt_2) if receipt_2 else 0
    
    # Pack into 210-bit integer (Two points + exact Arabic + HMAC tag)
    payload_210 = pack_all_210bits(
        name=name,
        lon=float(lon),
        lat=float(lat),
        lon_2=float(lon_2),
        lat_2=float(lat_2),
        receipt_1=r1,
        receipt_2=r2,
        center_id=cid,
        date_val=date_val
    )
    
    # Encrypt using ChaCha20 stream cipher (exact 210 bits)
    encrypted_210 = encrypt_210bits(payload_210)
    
    # Encode to Base58 (exactly 36 characters)
    b58_str = b58encode_int(encrypted_210, min_length=36)
    
    # Format into 6 blocks of 6
    return format_token(b58_str, group_size=6, prefix="DUDC")

def verify_dudc_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a DUDC Cadastral Security Token (returns P1 and P2).
    """
    try:
        clean_b58 = parse_token(token)
        if len(clean_b58) < 30 or len(clean_b58) > 42:
            return {
                'is_valid': False,
                'status_message': 'طول الكود غير صحيح (يجب أن يتكون من 36 خانة)',
                'error_code': 'INVALID_LENGTH'
            }
            
        cipher_int = b58decode_int(clean_b58)
        plain_int = decrypt_210bits(cipher_int)
        is_valid, data = unpack_all_210bits(plain_int)
        
        if not is_valid:
            return {
                'is_valid': False,
                'status_message': 'تحذير: بصمة الأمان غير متطابقة! الكود مزور أو تم التلاعب به أو به خطأ في النقل.',
                'error_code': 'TAMPER_DETECTED'
            }
            
        cid = data.get('center_id', 0)
        cname = get_center_name(cid)
        lat_1 = data.get('lat_1', 0.0)
        lon_1 = data.get('lon_1', 0.0)
        lat_2 = data.get('lat_2', 0.0)
        lon_2 = data.get('lon_2', 0.0)
        has_p2 = data.get('has_p2', False)
        
        p1_gis = f'{lat_1:.6f}, {lon_1:.6f}'
        p2_gis = f'{lat_2:.6f}, {lon_2:.6f}'
        both_gis = f'P1: {lat_1:.6f}, {lon_1:.6f}\nP2: {lat_2:.6f}, {lon_2:.6f}'
        
        r1 = data.get('receipt_1', 0)
        r2 = data.get('receipt_2', 0)
        receipt_display = f'{r1} - {r2}' if (r2 and r2 > 0) else f'{r1}'
            
        return {
            'is_valid': True,
            'status_message': 'الشهادة أصلية 100% ومطابقة للسجلات الرسمية لمركز DUDC',
            'name': data.get('name', ''),
            'center_id': cid,
            'center_name': cname,
            'receipt_1': r1,
            'receipt_2': r2,
            'receipt_display': receipt_display,
            'lat_1': lat_1,
            'lon_1': lon_1,
            'lat_2': lat_2,
            'lon_2': lon_2,
            'has_p2': has_p2,
            'coords_p1': p1_gis,
            'coords_p2': p2_gis,
            'coords_gis': both_gis,
            'issue_date': data.get('issue_date', '')
        }
    except Exception as e:
        return {
            'is_valid': False,
            'status_message': f'خطأ أثناء فك التشفير: {str(e)}',
            'error_code': 'DECODE_ERROR'
        }
