"""
DUDC Secure Token Client (Cloud-Isolated Microservice Edition)
=============================================================
Communicates directly with the secure Modal.com Cloud Service.
Zero cryptographic keys, zero Feistel ciphers, and zero salts reside
on the client generator machine.
"""

import json
import urllib.request
from typing import Union, Any, Dict

# Modal Cloud Live Endpoints
CLOUD_ENDPOINT = "https://killd00zer--dudc-security-service-generate-token-endpoint.modal.run"
CONFIRM_ENDPOINT = "https://killd00zer--dudc-security-service-confirm-issuance-endpoint.modal.run"
OFFICE_API_KEY = "DUDC_DAKAHLIA_OFFICE_SECRET_2026_KEY"

def generate_dudc_token(
    name: str,
    lon: float,
    lat: float,
    lon_2: float = 0.0,
    lat_2: float = 0.0,
    receipt_1: Union[int, str] = 0,
    receipt_2: Union[int, str] = 0,
    center: Union[int, str] = "المنصورة",
    date_val: Any = None,
    system_officer: str = "",
    survey_technician: str = "",
    **kwargs
) -> str:
    """
    Request security token from DUDC Modal Cloud Microservice via HTTPS JSON API.
    """
    payload = {
        "api_key": OFFICE_API_KEY,
        "name": str(name).strip(),
        "lon": float(lon),
        "lat": float(lat),
        "receipt_1": int(receipt_1) if receipt_1 else 0,
        "receipt_2": int(receipt_2) if receipt_2 else 0,
        "center": center,
        "date_val": str(date_val) if date_val else None,
        "system_officer": str(system_officer).strip(),
        "survey_technician": str(survey_technician).strip()
    }
    
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLOUD_ENDPOINT,
        data=req_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DUDC-V3-Generator/1.0"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("success"):
                return res_data.get("token")
            else:
                raise RuntimeError(f"Cloud Token Error: {res_data.get('error')}")
    except Exception as e:
        raise RuntimeError(f"فشل الاتصال بمنظومة التشفير السحابية: {str(e)}")

def confirm_cloud_issuance(token: str) -> Dict[str, Any]:
    """
    Confirm certificate issuance in Modal cloud audit log for official printing.
    """
    payload = {
        "api_key": OFFICE_API_KEY,
        "token": str(token).strip()
    }
    req_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CONFIRM_ENDPOINT,
        data=req_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "DUDC-V3-Generator/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"فشل الاتصال بسيرفر الاعتماد السحابي: {str(e)}")
