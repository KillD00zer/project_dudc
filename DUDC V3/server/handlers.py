"""
REST API Handlers & HTTP Dispatcher
===================================
Dispatches GET and POST requests cleanly to domain services and core GIS engines.
"""

import os
import re
import json
import time
import shutil
import base64
import tempfile
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Tuple

from core_gis.geo import read_survey_file
from core_gis.croquis import generate_croquis_image
from core_gis.satellite import generate_satellite_image
from core_gis.security import confirm_cloud_issuance, TRIAL_TOKEN
from core_gis.jurisdictions import resolve_center, get_center_name, list_all_centers

from .config import (
    APP_DIR,
    INDEX_HTML,
    SAMPLE_FILE,
    DEFAULTS_FILE,
    DRAFTS_DIR,
    TEMP_ASSETS_DIR,
    ASSETS_DIR,
    open_folder_picker,
    save_persistent_config,
    validate_or_fallback_output_dir,
    get_safe_default_output_dir,
    get_quick_locations,
    get_system_drives,
    list_subdirectories,
    create_subdirectory,
    validate_path_status,
)
from .pdf_service import export_certificate_pdf
from .git_service import check_git_updates, perform_git_update
from .drafts_service import list_drafts, save_draft, load_draft, delete_draft
from .session_manager import SESSION_MANAGER


def handle_get(req_handler, path: str) -> bool:
    """
    Handles GET requests. Returns True if handled.
    """
    parsed = urllib.parse.urlparse(path)
    clean_path = parsed.path

    if clean_path in ('/', '/index.html'):
        req_handler._send_file(INDEX_HTML, 'text/html; charset=utf-8')
        return True

    elif clean_path == '/api/health':
        req_handler._send_json({"status": "online", "version": "3.5", "timestamp": time.time()})
        return True

    elif clean_path == '/api/check-update':
        req_handler._send_json(check_git_updates())
        return True

    elif clean_path == '/api/get-output-dir':
        out_dir = SESSION_MANAGER.get_output_dir()
        req_handler._send_json({"output_dir": out_dir})
        return True

    elif clean_path == '/api/quick-locations':
        cur_out = SESSION_MANAGER.get_output_dir()
        req_handler._send_json({
            "success": True,
            "locations": get_quick_locations(),
            "drives": get_system_drives(),
            "current_output_dir": cur_out
        })
        return True

    elif clean_path == '/api/get-defaults':
        if os.path.exists(DEFAULTS_FILE):
            try:
                with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                req_handler._send_json({"success": True, "defaults": data})
                return True
            except Exception:
                pass
        req_handler._send_json({"success": False, "defaults": None})
        return True

    elif clean_path == '/api/get-centers':
        req_handler._send_json({"centers": list_all_centers()})
        return True

    elif clean_path == '/api/list-drafts':
        try:
            drafts = list_drafts()
            req_handler._send_json({"success": True, "drafts": drafts, "count": len(drafts)})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # Static CSS
    elif clean_path.startswith('/css/'):
        rel_path = clean_path.lstrip('/')
        full_path = os.path.join(APP_DIR, rel_path)
        req_handler._send_file(full_path, 'text/css; charset=utf-8')
        return True

    # Static JS
    elif clean_path.startswith('/js/'):
        rel_path = clean_path.lstrip('/')
        full_path = os.path.join(APP_DIR, rel_path)
        req_handler._send_file(full_path, 'application/javascript; charset=utf-8')
        return True

    # Static Assets (Images, Icons)
    elif clean_path.startswith('/assets/'):
        rel_path = clean_path.lstrip('/')
        full_path = os.path.join(APP_DIR, rel_path)
        ext = os.path.splitext(full_path)[1].lower()
        mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else ('image/png' if ext == '.png' else ('image/x-icon' if ext == '.ico' else 'application/octet-stream'))
        req_handler._send_file(full_path, mime)
        return True

    # Temp Assets (Rendered Croquis & Satellite JPEGs)
    elif clean_path.startswith('/temp_assets/'):
        fname = os.path.basename(clean_path)
        fpath = os.path.join(TEMP_ASSETS_DIR, fname)
        ext = os.path.splitext(fname)[1].lower()
        mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
        req_handler._send_file(fpath, mime)
        return True

    return False


def handle_post(req_handler, path: str, body_bytes: bytes) -> bool:
    """
    Handles POST requests. Returns True if handled.
    """
    parsed = urllib.parse.urlparse(path)
    clean_path = parsed.path

    # 1. Load Sample File (ف.xls)
    if clean_path == '/api/load-sample':
        try:
            if not os.path.exists(SAMPLE_FILE):
                req_handler._send_json({"error": "Sample file ف.xls not found"}, status=404)
                return True
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            sys_officer = req_data.get('system_officer', 'شريف محمد')
            survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
            raw_parcels = read_survey_file(SAMPLE_FILE)
            parcels = SESSION_MANAGER.enrich_parcels_with_security_tokens(raw_parcels, system_officer=sys_officer, survey_technician=survey_tech)
            SESSION_MANAGER.set_survey_data(parcels, SAMPLE_FILE, "ف.xls")

            req_handler._send_json({
                "success": True,
                "filename": "ف.xls",
                "total": len(parcels),
                "parcels": parcels,
                "official_centers": list_all_centers()
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 2. Upload Custom Survey File (.xls, .xlsx, .csv)
    elif clean_path == '/api/upload':
        try:
            content_type = req_handler.headers.get('Content-Type', '')

            if 'multipart/form-data' in content_type:
                boundary = content_type.split("boundary=")[1].encode()
                parts = body_bytes.split(boundary)

                saved_path = None
                orig_filename = "survey_file.csv"
                sys_officer = "شريف محمد"
                survey_tech = "محمد ابراهيم بدير"

                for part in parts:
                    if b'name="system_officer"' in part:
                        try:
                            _, v_body = part.split(b'\r\n\r\n', 1)
                            sys_officer = v_body.decode('utf-8', errors='ignore').split('\r\n')[0].strip()
                        except Exception:
                            pass
                    if b'name="survey_technician"' in part:
                        try:
                            _, v_body = part.split(b'\r\n\r\n', 1)
                            survey_tech = v_body.decode('utf-8', errors='ignore').split('\r\n')[0].strip()
                        except Exception:
                            pass
                    if b'filename="' in part:
                        header_part, file_body = part.split(b'\r\n\r\n', 1)
                        file_body = file_body.rstrip(b'\r\n--')
                        header_str = header_part.decode('utf-8', errors='ignore')

                        match = re.search(r'filename="([^"]+)"', header_str)
                        if match:
                            orig_filename = os.path.basename(match.group(1))

                        ext = os.path.splitext(orig_filename)[1].lower()
                        if ext not in ('.xls', '.xlsx', '.csv'):
                            ext = '.csv'

                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=TEMP_ASSETS_DIR)
                        tfile.write(file_body)
                        tfile.close()
                        saved_path = tfile.name
                        break

                if not saved_path or not os.path.exists(saved_path):
                    req_handler._send_json({"error": "Failed to receive uploaded file"}, status=400)
                    return True

                raw_parcels = read_survey_file(saved_path)
                parcels = SESSION_MANAGER.enrich_parcels_with_security_tokens(raw_parcels, system_officer=sys_officer, survey_technician=survey_tech)
                SESSION_MANAGER.set_survey_data(parcels, saved_path, orig_filename)

                req_handler._send_json({
                    "success": True,
                    "filename": orig_filename,
                    "total": len(parcels),
                    "parcels": parcels,
                    "official_centers": list_all_centers()
                })

            elif 'application/json' in content_type:
                req_data = json.loads(body_bytes.decode('utf-8'))
                fpath = req_data.get('file_path')
                if not fpath or not os.path.exists(fpath):
                    req_handler._send_json({"error": "File path does not exist"}, status=400)
                    return True
                raw_parcels = read_survey_file(fpath)
                parcels = SESSION_MANAGER.enrich_parcels_with_security_tokens(raw_parcels)
                SESSION_MANAGER.set_survey_data(parcels, fpath, os.path.basename(fpath))

                req_handler._send_json({
                    "success": True,
                    "filename": os.path.basename(fpath),
                    "total": len(parcels),
                    "parcels": parcels,
                    "official_centers": list_all_centers()
                })
            else:
                req_handler._send_json({"error": "Unsupported upload format"}, status=400)
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 3. Preview Satellite
    elif clean_path == '/api/preview-satellite':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            p_idx = req_data.get('parcel_index', 0)
            parcel = SESSION_MANAGER.get_parcel(p_idx)

            if not parcel:
                req_handler._send_json({"error": "No parcel available"}, status=400)
                return True

            pid = parcel.get("parcel_id", "0")
            sat_name = f"sat_{pid}.jpg"
            sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)

            generate_satellite_image(parcel, sat_path)

            req_handler._send_json({
                "success": True,
                "image_url": f"/temp_assets/{sat_name}?t={int(time.time())}"
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 4. Preview CAD Croquis
    elif clean_path == '/api/preview-croquis':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            p_idx = req_data.get('parcel_index', 0)
            parcel = SESSION_MANAGER.get_parcel(p_idx)

            if not parcel:
                req_handler._send_json({"error": "No parcel available"}, status=400)
                return True

            pid = parcel.get("parcel_id", "0")

            if "boundaries" in req_data:
                parcel["boundaries"] = req_data["boundaries"]

            if "edited_segments" in req_data:
                for i, s_data in enumerate(req_data["edited_segments"]):
                    if i < len(parcel.get("segments", [])):
                        if "length_m" in s_data:
                            try:
                                parcel["segments"][i]["length_m"] = round(float(s_data["length_m"]), 2)
                            except (ValueError, TypeError):
                                pass
                        if "direction" in s_data:
                            parcel["segments"][i]["direction"] = s_data["direction"]
                        if "neighbor" in s_data:
                            parcel["segments"][i]["neighbor"] = s_data["neighbor"]

            font_size_pts = int(req_data.get('font_size_pts', parcel.get("font_size_pts", 16)))
            font_size_dims = int(req_data.get('font_size_dims', parcel.get("font_size_dims", 16)))
            font_size_text = int(req_data.get('font_size_text', parcel.get("font_size_text", 16)))

            parcel["font_size_pts"] = font_size_pts
            parcel["font_size_dims"] = font_size_dims
            parcel["font_size_text"] = font_size_text

            croq_name = f"croq_{pid}.png"
            croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
            generate_croquis_image(
                parcel,
                croq_path,
                security_token=parcel.get("security_token") or TRIAL_TOKEN,
                font_size_pts=font_size_pts,
                font_size_dims=font_size_dims,
                font_size_text=font_size_text
            )

            sat_name = f"sat_{pid}.jpg"
            sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
            if not os.path.exists(sat_path):
                generate_satellite_image(parcel, sat_path)

            req_handler._send_json({
                "success": True,
                "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}",
                "satellite_url": f"/temp_assets/{sat_name}?t={int(time.time())}"
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 4.5 Upload Custom Parcel Image (Croquis or Satellite) from User Device
    elif clean_path == '/api/upload-parcel-image':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            target_type = req_data.get('type', 'croquis')
            b64_data = req_data.get('image_base64', '')
            p_idx = req_data.get('parcel_index', 0)

            pid = "0"
            parcel = SESSION_MANAGER.get_parcel(p_idx)
            if parcel:
                pid = parcel.get("parcel_id", "0")

            if b64_data and 'data:' in b64_data and ',' in b64_data:
                img_bytes = base64.b64decode(b64_data.split(',', 1)[1])
                out_path = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png" if target_type == 'croquis' else f"sat_{pid}.jpg")
                with open(out_path, 'wb') as f:
                    f.write(img_bytes)
                req_handler._send_json({"success": True, "saved_path": out_path})
            else:
                req_handler._send_json({"error": "Invalid base64 image data"}, status=400)
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 5. Output Directory Management
    elif clean_path == '/api/browse-output-dir':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            current_out = SESSION_MANAGER.get_output_dir()
            init_dir = req_data.get('initial_dir') or current_out
            folder = open_folder_picker(init_dir, current_out)
            if folder:
                current_out = SESSION_MANAGER.set_output_dir(folder)
                req_handler._send_json({"success": True, "folder_path": current_out, "output_dir": current_out})
            else:
                req_handler._send_json({"success": False, "folder_path": "", "output_dir": current_out})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    elif clean_path == '/api/browse-directory':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            target_path = req_data.get('path') or SESSION_MANAGER.get_output_dir()
            res = list_subdirectories(target_path)
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"success": False, "error": str(e)}, status=500)
        return True

    elif clean_path == '/api/create-directory':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            parent_path = req_data.get('parent_path')
            folder_name = req_data.get('folder_name', '')
            res = create_subdirectory(parent_path, folder_name)
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"success": False, "error": str(e)}, status=500)
        return True

    elif clean_path == '/api/validate-path':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            target_path = req_data.get('path', '')
            res = validate_path_status(target_path)
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"valid": False, "message": str(e)}, status=500)
        return True

    elif clean_path == '/api/set-output-dir':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            new_dir = req_data.get('output_dir', '').strip()
            saved_dir = SESSION_MANAGER.set_output_dir(new_dir)
            req_handler._send_json({"success": True, "output_dir": saved_dir})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 5.5 Update Center
    elif clean_path == '/api/update-center':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            p_idx = req_data.get('parcel_index', 0)
            parcel = SESSION_MANAGER.get_parcel(p_idx)

            if not parcel:
                req_handler._send_json({"error": "No parcel available to update center"}, status=400)
                return True

            raw_choice = req_data.get('center_id')
            if raw_choice is None:
                raw_choice = req_data.get('center_name', '')

            try:
                c_int = int(raw_choice)
                if 0 <= c_int < 18:
                    cid = c_int
                    canon_name = get_center_name(cid)
                    is_matched = True
                else:
                    is_matched, cid, canon_name = resolve_center(str(raw_choice))
            except (ValueError, TypeError):
                is_matched, cid, canon_name = resolve_center(str(raw_choice))

            if not is_matched or cid < 0 or cid > 17:
                req_handler._send_json({"error": "المركز المختار غير مسجل في القاموس الرسمي"}, status=400)
                return True

            survey_tech = req_data.get('survey_technician', '')
            sys_officer = req_data.get('system_officer', '')
            if survey_tech:
                parcel["survey_technician"] = survey_tech
            if sys_officer:
                parcel["system_officer"] = sys_officer

            parcel["district"] = canon_name
            parcel["district_id"] = cid
            parcel["district_matched"] = True
            parcel["security_token"] = None

            pid = parcel.get("parcel_id", "0")
            croq_name = f"croq_{pid}.png"
            croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
            generate_croquis_image(
                parcel,
                croq_path,
                security_token=TRIAL_TOKEN,
                font_size_pts=parcel.get("font_size_pts", 16),
                font_size_dims=parcel.get("font_size_dims", 16),
                font_size_text=parcel.get("font_size_text", 16)
            )

            req_handler._send_json({
                "success": True,
                "district": canon_name,
                "district_id": cid,
                "district_matched": True,
                "security_token": None,
                "trial_token": TRIAL_TOKEN,
                "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}"
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 6. Export Package
    elif clean_path == '/api/export-package':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            p_idx = req_data.get('parcel_index', 0)
            parcel = SESSION_MANAGER.get_parcel(p_idx)

            if not parcel:
                req_handler._send_json({"error": "No parcel available to export"}, status=400)
                return True

            pid = parcel.get("parcel_id", "0")
            citizen_name = req_data.get('applicant_name') or parcel.get("applicant_name", f"citizen_{pid}")
            district_name = req_data.get('district') or req_data.get('session_data', {}).get('district') or parcel.get("district", "")

            clean_name = re.sub(r'[\\/*?:"<>|]', '_', citizen_name.strip())
            clean_dist = re.sub(r'[\\/*?:"<>|]', '_', district_name.strip())

            out_dir = SESSION_MANAGER.get_output_dir()
            file_base_name = f"{clean_name}-{clean_dist}" if clean_dist else clean_name
            citizen_dir = os.path.join(out_dir, file_base_name)

            try:
                os.makedirs(citizen_dir, exist_ok=True)
            except Exception:
                out_dir = get_safe_default_output_dir()
                SESSION_MANAGER.set_output_dir(out_dir)
                citizen_dir = os.path.join(out_dir, file_base_name)
                os.makedirs(citizen_dir, exist_ok=True)

            croq_target_path = os.path.join(citizen_dir, f"croquis_{clean_name}.png")
            sat_target_path = os.path.join(citizen_dir, f"satellite_{clean_name}.jpg")

            c_b64 = req_data.get('croquis_base64', '')
            if c_b64 and 'data:' in c_b64 and ',' in c_b64:
                try:
                    c_data = base64.b64decode(c_b64.split(',', 1)[1])
                    with open(croq_target_path, 'wb') as f:
                        f.write(c_data)
                except Exception as e:
                    print(f"[!] Croquis base64 decode error: {e}")
            else:
                src_croq = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png")
                if os.path.exists(src_croq):
                    shutil.copy2(src_croq, croq_target_path)
                else:
                    generate_croquis_image(
                        parcel,
                        croq_target_path,
                        security_token=parcel.get("security_token"),
                        font_size_pts=parcel.get("font_size_pts", 16),
                        font_size_dims=parcel.get("font_size_dims", 16),
                        font_size_text=parcel.get("font_size_text", 16)
                    )

            s_b64 = req_data.get('satellite_base64', '')
            if s_b64 and 'data:' in s_b64 and ',' in s_b64:
                try:
                    s_data = base64.b64decode(s_b64.split(',', 1)[1])
                    with open(sat_target_path, 'wb') as f:
                        f.write(s_data)
                except Exception as e:
                    print(f"[!] Satellite base64 decode error: {e}")
            else:
                src_sat = os.path.join(TEMP_ASSETS_DIR, f"sat_{pid}.jpg")
                if os.path.exists(src_sat):
                    shutil.copy2(src_sat, sat_target_path)
                else:
                    generate_satellite_image(parcel, sat_target_path)

            croq_b64_embed = ""
            sat_b64_embed = ""
            if os.path.exists(croq_target_path):
                with open(croq_target_path, 'rb') as f:
                    croq_b64_embed = "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
            if os.path.exists(sat_target_path):
                with open(sat_target_path, 'rb') as f:
                    sat_b64_embed = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')

            survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
            sys_officer = req_data.get('system_officer', 'شريف محمد')
            parcel["survey_technician"] = survey_tech
            parcel["system_officer"] = sys_officer

            existing_token = parcel.get("security_token") or req_data.get('session_data', {}).get('security_token') or req_data.get('security_token')
            if not existing_token and parcel.get("district_id") is not None:
                try:
                    cid = parcel.get("district_id")
                    existing_token = SESSION_MANAGER.generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
                    confirm_cloud_issuance(existing_token)
                except Exception as te:
                    req_handler._send_json({"error": f"فشل إصدار كود الأمان من سيرفر Modal السحابي: {te}. لا يمكن تصدير الشهادة بدون توثيق كود الأمان رسمياً بالسجل المركزي."}, status=500)
                    return True

            if existing_token:
                parcel["security_token"] = existing_token

            pdf_out_path = os.path.join(citizen_dir, f"{file_base_name}.pdf")
            cert_html = req_data.get('certificate_html', '')
            pdf_created = False
            if cert_html:
                pdf_created = export_certificate_pdf(cert_html, pdf_out_path)

            json_path = os.path.join(citizen_dir, f"{file_base_name}_session.json")
            session_state = req_data.get('session_data', {})
            session_state["exported_at"] = datetime.now().isoformat()
            session_state["citizen_folder"] = citizen_dir
            session_state["applicant_name"] = clean_name
            session_state["district"] = clean_dist
            session_state["file_base_name"] = file_base_name
            if croq_b64_embed:
                session_state["croquis_base64"] = croq_b64_embed
            if sat_b64_embed:
                session_state["satellite_base64"] = sat_b64_embed
            if "parcel" in session_state and isinstance(session_state["parcel"], dict):
                if croq_b64_embed:
                    session_state["parcel"]["croquis_base64"] = croq_b64_embed
                if sat_b64_embed:
                    session_state["parcel"]["satellite_base64"] = sat_b64_embed

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(session_state, f, ensure_ascii=False, indent=2)

            archived_survey_file = None
            if SESSION_MANAGER.current_survey_file_path and os.path.exists(SESSION_MANAGER.current_survey_file_path):
                fname = SESSION_MANAGER.current_survey_filename or os.path.basename(SESSION_MANAGER.current_survey_file_path)
                target_survey_path = os.path.join(citizen_dir, fname)
                shutil.copy2(SESSION_MANAGER.current_survey_file_path, target_survey_path)
                archived_survey_file = fname

            try:
                target_draft_id = req_data.get('draft_id') or req_data.get('session_data', {}).get('draft_id')
                if target_draft_id:
                    delete_draft(target_draft_id)
            except Exception as de:
                print(f"[!] Warning deleting draft on export: {de}")

            req_handler._send_json({
                "success": True,
                "citizen_name": clean_name,
                "district": clean_dist,
                "file_base_name": file_base_name,
                "folder_path": citizen_dir,
                "files": {
                    "pdf": f"{file_base_name}.pdf" if pdf_created else None,
                    "session_json": f"{file_base_name}_session.json",
                    "croquis": f"croquis_{clean_name}.png",
                    "satellite": f"satellite_{clean_name}.jpg",
                    "survey_input": archived_survey_file
                }
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 7. Open Folder
    elif clean_path == '/api/open-folder':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            target = req_data.get('folder_path') or SESSION_MANAGER.get_output_dir()
            target = validate_or_fallback_output_dir(target)
            os.makedirs(target, exist_ok=True)
            os.startfile(target)
            req_handler._send_json({"success": True, "opened_path": target})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 8. Confirm Issuance
    elif clean_path == '/api/confirm-issuance':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            p_idx = req_data.get('parcel_index', 0)
            parcel = SESSION_MANAGER.get_parcel(p_idx)

            if not parcel:
                if req_data.get('parcel') and isinstance(req_data['parcel'], dict):
                    SESSION_MANAGER.set_parcels([req_data['parcel']])
                    parcel = SESSION_MANAGER.get_parcel(0)
                else:
                    req_handler._send_json({"error": "لا توجد قطعة مساحية نشطة للاعتماد"}, status=400)
                    return True

            for field in ('applicant_name', 'national_id', 'receipt_no', 'village', 'address', 'order_no', 'deal_type', 'site_desc', 'survey_technician', 'system_officer'):
                if req_data.get(field):
                    parcel[field] = req_data[field].strip()

            if req_data.get('district'):
                raw_d = req_data['district'].strip()
                is_m, cid_res, cname = resolve_center(raw_d)
                if is_m:
                    parcel["district"] = cname
                    parcel["district_id"] = cid_res
                    parcel["district_matched"] = True

            cid = parcel.get("district_id")
            if cid is None:
                is_m, cid_res, cname = resolve_center(parcel.get("district", "المنصورة"))
                cid = cid_res if is_m else 0
                if is_m:
                    parcel["district"] = cname

            sys_officer = parcel.get("system_officer", "شريف محمد")
            survey_tech = parcel.get("survey_technician", "محمد ابراهيم بدير")

            official_token = SESSION_MANAGER.generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
            parcel["security_token"] = official_token

            conf_res = confirm_cloud_issuance(official_token)
            if not conf_res.get("success"):
                raise RuntimeError(conf_res.get("error", "فشل توثيق الشهادة في السجل السحابي الرسمي"))

            pid = parcel.get("parcel_id", "0")
            croq_name = f"croq_{pid}.png"
            croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
            generate_croquis_image(
                parcel,
                croq_path,
                security_token=official_token,
                font_size_pts=parcel.get("font_size_pts", 16),
                font_size_dims=parcel.get("font_size_dims", 16),
                font_size_text=parcel.get("font_size_text", 16)
            )

            req_handler._send_json({
                "success": True,
                "token": official_token,
                "confirmed_at": conf_res.get("confirmed_at", datetime.now().strftime("%Y/%m/%d %H:%M:%S")),
                "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}",
                "message": "تم إصدار وتوثيق كود الأمان الرسمي بنجاح في السجل السحابي"
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 9. Save / Reset Defaults
    elif clean_path == '/api/save-defaults':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            with open(DEFAULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(req_data, f, ensure_ascii=False, indent=2)
            req_handler._send_json({"success": True, "message": "تم حفظ الإعدادات الافتراضية بنجاح"})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    elif clean_path == '/api/reset-defaults':
        try:
            if os.path.exists(DEFAULTS_FILE):
                os.remove(DEFAULTS_FILE)
            req_handler._send_json({"success": True, "message": "تم استعادة الإعدادات الأصلية بنجاح"})
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 10. Restore Session
    elif clean_path == '/api/restore-session':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            parcel = req_data.get('parcel')
            if not parcel:
                req_handler._send_json({"error": "بيانات المعاملة غير متوفرة في ملف الجلسة"}, status=400)
                return True

            pid = parcel.get('parcel_id', '0')
            SESSION_MANAGER.set_parcels([parcel])

            croq_name = f"croq_{pid}.png"
            croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
            croq_b64 = req_data.get('croquis_base64')
            if croq_b64 and isinstance(croq_b64, str) and 'data:image' in croq_b64:
                try:
                    c_raw = croq_b64.split(',', 1)[1] if ',' in croq_b64 else croq_b64
                    with open(croq_path, 'wb') as f:
                        f.write(base64.b64decode(c_raw))
                except Exception as ce:
                    print(f"[!] Warning decoding croquis: {ce}")
            elif not os.path.exists(croq_path) and parcel.get('vertices'):
                generate_croquis_image(parcel, croq_path, security_token=parcel.get('security_token'))

            sat_name = f"sat_{pid}.jpg"
            sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
            sat_b64 = req_data.get('satellite_base64')
            if sat_b64 and isinstance(sat_b64, str) and 'data:image' in sat_b64:
                try:
                    s_raw = sat_b64.split(',', 1)[1] if ',' in sat_b64 else sat_b64
                    with open(sat_path, 'wb') as f:
                        f.write(base64.b64decode(s_raw))
                except Exception as se:
                    print(f"[!] Warning decoding satellite: {se}")
            elif not os.path.exists(sat_path) and parcel.get('vertices'):
                generate_satellite_image(parcel, sat_path)

            req_handler._send_json({
                "success": True,
                "message": "تم استعادة الجلسة في السيرفر بنجاح",
                "parcel": parcel,
                "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}" if os.path.exists(croq_path) else None,
                "satellite_url": f"/temp_assets/{sat_name}?t={int(time.time())}" if os.path.exists(sat_path) else None
            })
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 11. Drafts: Save / Load / Delete
    elif clean_path == '/api/save-draft':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            res = save_draft(req_data)
            p = req_data.get("parcel") or req_data.get("session_data", {}).get("parcel", {})
            if p and isinstance(p, dict) and p.get('applicant_name'):
                SESSION_MANAGER.set_parcels([p])
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    elif clean_path == '/api/load-draft':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            draft_id = req_data.get('draft_id', '').strip()
            if not draft_id:
                req_handler._send_json({"error": "معرف المسودة مطلوب"}, status=400)
                return True
            res = load_draft(draft_id)
            if "error" in res:
                req_handler._send_json(res, status=res.get("status", 400))
                return True
            p = res.get("draft", {}).get("parcel") or res.get("draft", {}).get("session_data", {}).get("parcel")
            if p and isinstance(p, dict):
                SESSION_MANAGER.set_parcels([p])
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    elif clean_path == '/api/delete-draft':
        try:
            req_data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            draft_id = req_data.get('draft_id', '').strip()
            if not draft_id:
                req_handler._send_json({"error": "معرف المسودة مطلوب للحذف"}, status=400)
                return True
            res = delete_draft(draft_id)
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"error": str(e)}, status=500)
        return True

    # 12. Git Update
    elif clean_path == '/api/perform-update':
        try:
            res = perform_git_update()
            req_handler._send_json(res)
        except Exception as e:
            req_handler._send_json({"success": False, "error": str(e)}, status=500)
        return True

    return False
