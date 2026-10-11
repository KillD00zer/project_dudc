"""
Thread-Safe Session & State Manager
===================================
Manages in-memory active parcels, survey files, and output paths safely
using synchronization locks to eliminate race conditions.
"""

import threading
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from core_gis.security import generate_dudc_token
from core_gis.jurisdictions import resolve_center
import os
import json
import base64
from .config import load_saved_config, save_persistent_config, validate_or_fallback_output_dir, get_safe_default_output_dir, TEMP_ASSETS_DIR

ARABIC_DAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
ARABIC_TO_ENG = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def to_arabic_numerals(text: Any) -> str:
    if text is None:
        return ""
    return str(text).translate(ARABIC_TO_ENG)


to_english_numerals = to_arabic_numerals


def format_issue_date(issue_date_val: Any = None) -> Tuple[str, str]:
    if isinstance(issue_date_val, str) and issue_date_val.strip():
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(issue_date_val.strip(), fmt)
                break
            except ValueError:
                dt = datetime.now()
    elif isinstance(issue_date_val, datetime):
        dt = issue_date_val
    else:
        dt = datetime.now()

    day_name = ARABIC_DAYS[dt.weekday()]
    date_str = f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    display_text = f"تحريراً في : {day_name} الموافق {date_str}"
    iso_date = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
    return display_text, iso_date


class SessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self.current_parcels: List[Dict[str, Any]] = []
        self.current_survey_file_path: Optional[str] = None
        self.current_survey_filename: Optional[str] = None
        self.active_session: Dict[str, Any] = {}

        cfg = load_saved_config()
        raw_out = cfg.get("output_dir")
        self.output_dir = validate_or_fallback_output_dir(raw_out)
        if raw_out and raw_out != self.output_dir:
            save_persistent_config("output_dir", self.output_dir)

    def get_output_dir(self) -> str:
        with self._lock:
            self.output_dir = validate_or_fallback_output_dir(self.output_dir)
            return self.output_dir

    def set_output_dir(self, new_dir: str) -> str:
        with self._lock:
            valid_dir = validate_or_fallback_output_dir(new_dir)
            self.output_dir = valid_dir
            save_persistent_config("output_dir", valid_dir)
            return valid_dir

    def set_survey_data(self, parcels: List[Dict[str, Any]], file_path: str, filename: str) -> None:
        with self._lock:
            self.current_parcels = parcels
            self.current_survey_file_path = file_path
            self.current_survey_filename = filename

    def get_parcels(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.current_parcels)

    def get_parcel(self, idx: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            if 0 <= idx < len(self.current_parcels):
                return self.current_parcels[idx]
            if self.active_session and isinstance(self.active_session, dict):
                p = self.active_session.get("parcel")
                if p:
                    self.current_parcels = [p]
                    return p
            return None

    def update_parcel(self, idx: int, data: Dict[str, Any]) -> None:
        with self._lock:
            if 0 <= idx < len(self.current_parcels):
                self.current_parcels[idx].update(data)
            elif not self.current_parcels:
                self.current_parcels = [data]

    def set_parcels(self, parcels: List[Dict[str, Any]]) -> None:
        with self._lock:
            self.current_parcels = parcels

    def enrich_parcels_with_security_tokens(
        self,
        parcels: List[Dict[str, Any]],
        system_officer: str = "",
        survey_technician: str = ""
    ) -> List[Dict[str, Any]]:
        now_dt = datetime.now()
        date_display, _ = format_issue_date(now_dt)
        for p in parcels:
            if system_officer:
                p["system_officer"] = system_officer
            if survey_technician:
                p["survey_technician"] = survey_technician

            raw_dist = p.get("district", "")
            is_matched, cid, canon_name = resolve_center(raw_dist)

            p["district_matched"] = is_matched
            p["district_id"] = cid if is_matched else None
            p["issue_date_display"] = date_display

            if is_matched:
                p["district"] = canon_name
            else:
                p["district"] = raw_dist

            p["security_token"] = None

        return parcels

    def generate_token_for_parcel(
        self,
        p: Dict[str, Any],
        center_id: int,
        system_officer: str = "",
        survey_technician: str = ""
    ) -> str:
        now_dt = datetime.now()
        verts = p.get("vertices", [])
        p1_lon = verts[0]["lon"] if verts else 31.381790
        p1_lat = verts[0]["lat"] if verts else 31.051135
        p2_lon = verts[1]["lon"] if len(verts) > 1 else p1_lon
        p2_lat = verts[1]["lat"] if len(verts) > 1 else p1_lat

        rcp_raw = str(p.get("receipt_no", "0")).replace(" ", "")
        rcp_parts = rcp_raw.split("-") if "-" in rcp_raw else [rcp_raw]
        try:
            r1 = int("".join(filter(str.isdigit, rcp_parts[0])))
        except ValueError:
            r1 = 0
        r2 = 0
        if len(rcp_parts) > 1:
            try:
                r2 = int("".join(filter(str.isdigit, rcp_parts[1])))
            except ValueError:
                r2 = 0

        officer = system_officer or p.get("system_officer", "")
        technician = survey_technician or p.get("survey_technician", "")

        return generate_dudc_token(
            name=p.get("applicant_name", ""),
            lon=p1_lon,
            lat=p1_lat,
            lon_2=p2_lon,
            lat_2=p2_lat,
            receipt_1=r1,
            receipt_2=r2,
            center=int(center_id),
            date_val=now_dt,
            system_officer=officer,
            survey_technician=technician
        )



    def update_active_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if not isinstance(session_data, dict):
                return dict(self.active_session)

            self.active_session.update(session_data)

            # Synchronize parcel in memory
            parcel = session_data.get("parcel") or self.active_session.get("parcel")
            if not parcel:
                parcel = dict(self.current_parcels[0]) if self.current_parcels else {}

            for field in [
                "applicant_name", "receipt_no", "national_id", "district", "district_id",
                "village", "address", "deal_type", "transaction_type", "site_desc", "site_status",
                "order_no", "request_no", "survey_technician", "system_officer", "security_token",
                "boundaries", "segments", "vertices", "stated_area_m2", "calculated_area_m2",
                "line_width", "font_size_pts", "font_size_dims", "font_size_text"
            ]:
                if field in session_data and session_data[field] is not None:
                    parcel[field] = session_data[field]

            self.active_session["parcel"] = parcel
            if self.current_parcels:
                self.current_parcels[0].update(parcel)
            else:
                self.current_parcels = [parcel]

            # Cache croquis image to disk if base64 provided
            croq_b64 = session_data.get("croquis_base64")
            if croq_b64 and isinstance(croq_b64, str) and "data:image" in croq_b64 and "," in croq_b64:
                try:
                    c_path = os.path.join(TEMP_ASSETS_DIR, "croq_0.png")
                    c_raw = croq_b64.split(",", 1)[1]
                    with open(c_path, "wb") as f:
                        f.write(base64.b64decode(c_raw))
                except Exception as ce:
                    pass

            # Cache satellite image to disk if base64 provided
            sat_b64 = session_data.get("satellite_base64")
            if sat_b64 and isinstance(sat_b64, str) and "data:image" in sat_b64 and "," in sat_b64:
                try:
                    s_path = os.path.join(TEMP_ASSETS_DIR, "sat_0.jpg")
                    s_raw = sat_b64.split(",", 1)[1]
                    with open(s_path, "wb") as f:
                        f.write(base64.b64decode(s_raw))
                except Exception as se:
                    pass

            # Write recovery snapshot to temp_assets/active_session.json
            try:
                state_file = os.path.join(TEMP_ASSETS_DIR, "active_session.json")
                snapshot = dict(self.active_session)
                if snapshot.get("croquis_base64") and len(snapshot["croquis_base64"]) > 500:
                    snapshot["croquis_base64"] = "/temp_assets/croq_0.png"
                if snapshot.get("satellite_base64") and len(snapshot["satellite_base64"]) > 500:
                    snapshot["satellite_base64"] = "/temp_assets/sat_0.jpg"
                with open(state_file, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            return dict(self.active_session)

    def get_active_session(self) -> Dict[str, Any]:
        with self._lock:
            if not self.active_session:
                state_file = os.path.join(TEMP_ASSETS_DIR, "active_session.json")
                if os.path.exists(state_file):
                    try:
                        with open(state_file, "r", encoding="utf-8") as f:
                            self.active_session = json.load(f)
                    except Exception:
                        pass
            return dict(self.active_session)

    def clear_session_cache(self, temp_assets_dir: str = "") -> dict:
        """
        Clears in-memory parcel state and optionally purges stale temp image files
        (croquis_*.png, satellite_*.jpg) from temp_assets_dir so that the next
        import starts from a completely clean slate with no stale cached images.
        """
        import glob
        import os

        deleted = []
        with self._lock:
            self.current_parcels = []
            self.current_survey_file_path = None
            self.current_survey_filename = None

        if temp_assets_dir and os.path.isdir(temp_assets_dir):
            patterns = [
                os.path.join(temp_assets_dir, "croq_*.png"),
                os.path.join(temp_assets_dir, "sat_*.jpg"),
                os.path.join(temp_assets_dir, "sat_*.jpeg"),
                os.path.join(temp_assets_dir, "croquis_*.png"),
                os.path.join(temp_assets_dir, "satellite_*.jpg"),
                os.path.join(temp_assets_dir, "satellite_*.jpeg"),
                os.path.join(temp_assets_dir, "cropped_*.png"),
                os.path.join(temp_assets_dir, "cropped_*.jpg"),
                os.path.join(temp_assets_dir, "temp_print_*.html"),
                os.path.join(temp_assets_dir, "tmp_*.*"),
            ]
            for pattern in patterns:
                for f in glob.glob(pattern):
                    try:
                        os.remove(f)
                        deleted.append(os.path.basename(f))
                    except OSError:
                        pass

        return {"cleared_files": deleted, "count": len(deleted)}


SESSION_MANAGER = SessionManager()
