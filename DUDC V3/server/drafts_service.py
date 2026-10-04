"""
Draft Management Service
========================
Handles persisting, retrieving, listing, and cleaning temporary certificate drafts (JSON)
with complete embedded base64 graphics for reliable recovery.
"""

import os
import json
import time
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional

from core_gis.croquis import generate_croquis_image
from core_gis.satellite import generate_satellite_image
from .config import DRAFTS_DIR, TEMP_ASSETS_DIR, ASSETS_DIR


def ensure_base64_image(img_input: Any, img_type: str = 'croquis', parcel: Optional[Dict] = None, pid: str = '0') -> str:
    """
    Ensures an image reference (base64, local path, or URL) is resolved to a complete,
    valid data:image/...;base64,... string for saving self-contained JSON drafts/sessions.
    """
    if img_input and isinstance(img_input, str) and img_input.startswith("data:image/"):
        return img_input

    target_disk_path = None
    if img_input and isinstance(img_input, str) and img_input.strip():
        clean = img_input.strip().split("?")[0]
        if "temp_assets/" in clean:
            fn = clean.split("temp_assets/")[-1]
            p = os.path.join(TEMP_ASSETS_DIR, fn)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                target_disk_path = p
        elif "assets/" in clean:
            fn = clean.split("assets/")[-1]
            p = os.path.join(ASSETS_DIR, fn)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                target_disk_path = p
        elif os.path.exists(clean) and os.path.isfile(clean) and os.path.getsize(clean) > 0:
            target_disk_path = clean

    if not target_disk_path:
        cand = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png" if img_type == "croquis" else f"sat_{pid}.jpg")
        if os.path.exists(cand) and os.path.getsize(cand) > 0:
            target_disk_path = cand

    if target_disk_path and os.path.exists(target_disk_path):
        try:
            mime = "image/png" if target_disk_path.lower().endswith(".png") else "image/jpeg"
            with open(target_disk_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"[!] Warning reading image {target_disk_path}: {e}")

    if parcel and isinstance(parcel, dict) and parcel.get("vertices"):
        try:
            if img_type == "croquis":
                out_p = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png")
                generate_croquis_image(
                    parcel,
                    out_p,
                    security_token=parcel.get("security_token"),
                    font_size_pts=parcel.get("font_size_pts", 16),
                    font_size_dims=parcel.get("font_size_dims", 16),
                    font_size_text=parcel.get("font_size_text", 16)
                )
                if os.path.exists(out_p) and os.path.getsize(out_p) > 0:
                    with open(out_p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                        return f"data:image/png;base64,{b64}"
            else:
                out_p = os.path.join(TEMP_ASSETS_DIR, f"sat_{pid}.jpg")
                generate_satellite_image(parcel, out_p)
                if os.path.exists(out_p) and os.path.getsize(out_p) > 0:
                    with open(out_p, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                        return f"data:image/jpeg;base64,{b64}"
        except Exception as ge:
            print(f"[!] Warning generating {img_type} for draft: {ge}")

    sample = os.path.join(ASSETS_DIR, "sample_croquis.png" if img_type == "croquis" else "sample_satellite.jpg")
    if os.path.exists(sample):
        mime = "image/png" if sample.lower().endswith(".png") else "image/jpeg"
        with open(sample, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"

    return ""


def list_drafts() -> List[Dict[str, Any]]:
    drafts = []
    if os.path.exists(DRAFTS_DIR):
        for fname in os.listdir(DRAFTS_DIR):
            if fname.endswith('.json'):
                fpath = os.path.join(DRAFTS_DIR, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        ddata = json.load(f)
                    drafts.append({
                        "draft_id": ddata.get("draft_id", fname.replace(".json", "")),
                        "applicant_name": ddata.get("applicant_name") or ddata.get("parcel", {}).get("applicant_name") or "بدون اسم",
                        "district": ddata.get("district") or ddata.get("parcel", {}).get("district") or "غير محدد",
                        "area": ddata.get("area") or ddata.get("parcel", {}).get("contract_area_text") or "--",
                        "saved_at": ddata.get("saved_at") or "",
                        "filename": fname
                    })
                except Exception:
                    pass
    drafts.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
    return drafts


def save_draft(req_data: Dict[str, Any]) -> Dict[str, Any]:
    draft_id = req_data.get('draft_id')
    if not draft_id:
        draft_id = f"draft_{int(time.time())}_{uuid.uuid4().hex[:6]}"

    file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
    draft_filename = f"{file_id}.json"
    draft_path = os.path.join(DRAFTS_DIR, draft_filename)

    req_data["draft_id"] = file_id
    req_data["saved_at"] = datetime.now().strftime("%Y/%m/%d %I:%M %p")

    p = req_data.get("parcel") or req_data.get("session_data", {}).get("parcel", {})
    pid = p.get('parcel_id', '0') if isinstance(p, dict) else '0'

    raw_croq = req_data.get("croquis_base64") or req_data.get("session_data", {}).get("croquis_base64")
    raw_sat = req_data.get("satellite_base64") or req_data.get("session_data", {}).get("satellite_base64")

    croq_b64 = ensure_base64_image(raw_croq, "croquis", parcel=p, pid=pid)
    sat_b64 = ensure_base64_image(raw_sat, "satellite", parcel=p, pid=pid)

    req_data["croquis_base64"] = croq_b64
    req_data["satellite_base64"] = sat_b64
    if "session_data" in req_data and isinstance(req_data["session_data"], dict):
        req_data["session_data"]["croquis_base64"] = croq_b64
        req_data["session_data"]["satellite_base64"] = sat_b64
        if "parcel" in req_data["session_data"] and isinstance(req_data["session_data"]["parcel"], dict):
            req_data["session_data"]["parcel"]["croquis_base64"] = croq_b64
            req_data["session_data"]["parcel"]["satellite_base64"] = sat_b64
    if "parcel" in req_data and isinstance(req_data["parcel"], dict):
        req_data["parcel"]["croquis_base64"] = croq_b64
        req_data["parcel"]["satellite_base64"] = sat_b64

    req_data["applicant_name"] = req_data.get("applicant_name") or (p.get("applicant_name") if isinstance(p, dict) else "بدون اسم")
    req_data["district"] = req_data.get("district") or (p.get("district") if isinstance(p, dict) else "غير محدد")
    req_data["area"] = req_data.get("area") or (p.get("contract_area_text") if isinstance(p, dict) else "--")

    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(req_data, f, ensure_ascii=False, indent=2)

    return {
        "success": True,
        "draft_id": file_id,
        "saved_at": req_data["saved_at"],
        "message": "تم حفظ المسودة بنجاح في صندوق مسودات اليوم"
    }


def load_draft(draft_id: str) -> Dict[str, Any]:
    file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
    draft_path = os.path.join(DRAFTS_DIR, f"{file_id}.json")
    if not os.path.exists(draft_path):
        return {"error": "المسودة غير موجودة أو تم حذفها", "status": 404}

    with open(draft_path, "r", encoding="utf-8") as f:
        draft_data = json.load(f)

    p = draft_data.get("parcel") or draft_data.get("session_data", {}).get("parcel")
    croq_url = None
    sat_url = None

    if p and isinstance(p, dict):
        pid = p.get('parcel_id', '0')

        croq_b64 = draft_data.get('croquis_base64') or draft_data.get('session_data', {}).get('croquis_base64')
        if croq_b64 and isinstance(croq_b64, str) and 'data:image' in croq_b64:
            try:
                c_raw = croq_b64.split(',', 1)[1] if ',' in croq_b64 else croq_b64
                croq_out = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png")
                with open(croq_out, 'wb') as f:
                    f.write(base64.b64decode(c_raw))
                croq_url = f"/temp_assets/croq_{pid}.png?t={int(time.time())}"
            except Exception as ce:
                print(f"[!] Error unpacking croquis: {ce}")

        sat_b64 = draft_data.get('satellite_base64') or draft_data.get('session_data', {}).get('satellite_base64')
        if sat_b64 and isinstance(sat_b64, str) and 'data:image' in sat_b64:
            try:
                s_raw = sat_b64.split(',', 1)[1] if ',' in sat_b64 else sat_b64
                sat_out = os.path.join(TEMP_ASSETS_DIR, f"sat_{pid}.jpg")
                with open(sat_out, 'wb') as f:
                    f.write(base64.b64decode(s_raw))
                sat_url = f"/temp_assets/sat_{pid}.jpg?t={int(time.time())}"
            except Exception as se:
                print(f"[!] Error unpacking satellite: {se}")

    return {
        "success": True,
        "draft_id": file_id,
        "draft": draft_data,
        "croquis_url": croq_url,
        "satellite_url": sat_url
    }


def delete_draft(draft_id: str) -> Dict[str, Any]:
    file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
    draft_path = os.path.join(DRAFTS_DIR, f"{file_id}.json")
    if os.path.exists(draft_path):
        os.remove(draft_path)
        return {"success": True, "message": "تم حذف المسودة بنجاح"}
    return {"success": True, "message": "المسودة غير موجودة بالفعل"}
