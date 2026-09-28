"""
DUDC V3.5 - Next-Generation Cadastral Certificate Workflow Server
================================================================
Dakahlia Utility Data Center (مركز معلومات شبكات المرافق)
Provides local REST API endpoints for the complete 3-Stage Workflow:
1. Stage 1: Survey Ingestion, Geodesic Validation, Satellite & Croquis Generation, Token Creation
2. Stage 2: Studio Edit, Contextual Typography, Image Crop & Zoom, Watermark Control
3. Stage 3: Direct Vector A4 PDF Print & Complete Citizen Package Export (PDF + DOCX + JSON + Images + Survey File)
"""

import sys
import os

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import re
import json
import shutil
import tempfile
import webbrowser
import base64
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime

# Local core engines
from geo_engine import read_survey_file
from satellite_engine import generate_satellite_image
from croquis_engine import generate_croquis_image
from docx_builder import generate_certificate_docx, format_issue_date
from encoder_api import generate_dudc_token, confirm_cloud_issuance
from centers import resolve_center, get_center_name, list_all_centers

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "app_config.json")
DEFAULTS_FILE = os.path.join(APP_DIR, "user_default_settings.json")

def load_saved_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_persistent_config(key, val):
    cfg = load_saved_config()
    cfg[key] = val
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

import threading as _threading
import subprocess as _subprocess
_folder_picker_lock = _threading.Lock()

def open_folder_picker(initial_dir=""):
    """
    Open Windows native folder picker via PowerShell only.
    - No Tkinter (crashes from non-main thread)
    - Threading lock prevents double-dialog if button clicked twice
    """
    # Non-blocking acquire: if dialog already open, return immediately
    if not _folder_picker_lock.acquire(blocking=False):
        return ""
    try:
        init_dir = (
            initial_dir
            if (initial_dir and os.path.exists(initial_dir))
            else (OUTPUT_DIR if os.path.exists(OUTPUT_DIR) else os.getcwd())
        )
        safe_dir = init_dir.replace("'", "''").replace('"', '')

        # Modern Windows Vista+ FolderBrowserDialog via PowerShell
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$d.ShowNewFolderButton = $true; "
            "try { $d.UseDescriptionForTitle = $true } catch {}; "
            "$d.Description = 'اختر مجلد حفظ الشهادات المساحية'; "
            f"$d.SelectedPath = '{safe_dir}'; "
            "if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
            "{ Write-Output $d.SelectedPath }"
        )
        res = _subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=180
        )
        out = res.stdout.strip()
        if out:
            return os.path.normpath(out)
        return ""
    except Exception:
        return ""
    finally:
        _folder_picker_lock.release()


_saved_cfg = load_saved_config()
OUTPUT_DIR = _saved_cfg.get("output_dir") or os.path.join(APP_DIR, "generated_certificates")
TEMP_ASSETS_DIR = os.path.join(APP_DIR, "temp_assets")
SAMPLE_FILE = os.path.join(APP_DIR, "ف.xls")
INDEX_HTML = os.path.join(APP_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_ASSETS_DIR, exist_ok=True)

CURRENT_PARCELS = []
CURRENT_SURVEY_FILE_PATH = None
CURRENT_SURVEY_FILENAME = None

def generate_token_for_parcel(p, center_id, system_officer="", survey_technician=""):
    """Generate authentic 210-bit DUDC security token with confirmed center ID & audit log."""
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

def enrich_parcels_with_security_tokens(parcels, system_officer="", survey_technician=""):
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
            try:
                p["security_token"] = generate_token_for_parcel(p, cid, system_officer=p.get("system_officer", ""), survey_technician=p.get("survey_technician", ""))
            except Exception as e:
                print(f"[!] Warning: Token error during enrich: {e}")
                p["security_token"] = None
        else:
            # Rule: Security token is NOT generated or shown until center is secured!
            p["district"] = raw_dist
            p["security_token"] = None

    return parcels

def export_certificate_pdf(cert_html, output_pdf_path):
    """
    Renders standalone certificate HTML to an official A4 PDF using Microsoft Edge headless.
    """
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_exe = None
    for ep in edge_paths:
        if os.path.exists(ep):
            edge_exe = ep
            break

    if not edge_exe:
        print("[!] Microsoft Edge not found; skipping headless PDF generation.")
        return False

    temp_html_path = os.path.join(TEMP_ASSETS_DIR, f"temp_print_{int(time.time()*1000)}.html")
    try:
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(cert_html)

        cmd = [
            edge_exe,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            f"--print-to-pdf={output_pdf_path}",
            temp_html_path
        ]
        res = _subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 0:
            return True
        else:
            print(f"[!] Edge PDF generation warning: {res.stderr or res.stdout}")
            return False
    except Exception as e:
        print(f"[!] Error exporting PDF via Edge: {e}")
        return False
    finally:
        if os.path.exists(temp_html_path):
            try:
                os.remove(temp_html_path)
            except Exception:
                pass

class DUDCV3RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path, content_type='text/html; charset=utf-8'):
        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return
        with open(file_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        global OUTPUT_DIR
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path in ('/', '/index.html'):
            self._send_file(INDEX_HTML, 'text/html; charset=utf-8')
        elif path == '/api/health':
            self._send_json({"status": "online", "version": "3.5", "timestamp": time.time()})
        elif path == '/api/get-output-dir':
            self._send_json({"output_dir": OUTPUT_DIR})
        elif path == '/api/get-defaults':
            if os.path.exists(DEFAULTS_FILE):
                try:
                    with open(DEFAULTS_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._send_json({"success": True, "defaults": data})
                    return
                except Exception:
                    pass
            self._send_json({"success": False, "defaults": None})
        elif path == '/api/get-centers':
            self._send_json({"centers": list_all_centers()})
        elif path.startswith('/assets/'):
            rel_path = path.lstrip('/')
            full_path = os.path.join(APP_DIR, rel_path)
            ext = os.path.splitext(full_path)[1].lower()
            mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else ('image/png' if ext == '.png' else 'application/octet-stream')
            self._send_file(full_path, mime)
        elif path.startswith('/temp_assets/'):
            fname = os.path.basename(path)
            fpath = os.path.join(TEMP_ASSETS_DIR, fname)
            ext = os.path.splitext(fname)[1].lower()
            mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
            self._send_file(fpath, mime)
        # 8. Confirm Certificate Issuance in Cloud
        elif path == '/api/confirm-issuance':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                token = req_data.get('token', '').strip()
                if not token:
                    self._send_json({"error": "الكود الأمني مطلوب للاعتماد"}, status=400)
                    return
                
                conf_res = confirm_cloud_issuance(token)
                self._send_json({
                    "success": True,
                    "token": token,
                    "confirmed_at": conf_res.get("confirmed_at", ""),
                    "message": "تم اعتماد الشهادة بنجاح وتسجيلها رسمي للطباعة"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        global CURRENT_PARCELS, CURRENT_SURVEY_FILE_PATH, CURRENT_SURVEY_FILENAME, OUTPUT_DIR
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # 1. Load Sample File (ف.xls)
        if path == '/api/load-sample':
            try:
                if not os.path.exists(SAMPLE_FILE):
                    self._send_json({"error": "Sample file ف.xls not found"}, status=404)
                    return
                length = int(self.headers.get('Content-Length', 0))
                req_data = json.loads(self.rfile.read(length).decode('utf-8')) if length > 0 else {}
                sys_officer = req_data.get('system_officer', 'شريف محمد')
                survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
                CURRENT_PARCELS = enrich_parcels_with_security_tokens(read_survey_file(SAMPLE_FILE), system_officer=sys_officer, survey_technician=survey_tech)
                CURRENT_SURVEY_FILE_PATH = SAMPLE_FILE
                CURRENT_SURVEY_FILENAME = "ف.xls"
                self._send_json({
                    "success": True,
                    "filename": "ف.xls",
                    "total": len(CURRENT_PARCELS),
                    "parcels": CURRENT_PARCELS,
                    "official_centers": list_all_centers()
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 2. Upload Custom Survey File (.xls, .xlsx, .csv)
        elif path == '/api/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                content_type = self.headers.get('Content-Type', '')

                if 'multipart/form-data' in content_type:
                    boundary = content_type.split("boundary=")[1].encode()
                    raw_data = self.rfile.read(content_length)
                    parts = raw_data.split(boundary)

                    saved_path = None
                    orig_filename = "survey_file.csv"
                    sys_officer = "شريف محمد"
                    survey_tech = "محمد ابراهيم بدير"

                    for part in parts:
                        if b'name="system_officer"' in part:
                            try:
                                _, v_body = part.split(b'\r\n\r\n', 1)
                                sys_officer = v_body.decode('utf-8', errors='ignore').split('\r\n')[0].strip()
                            except Exception: pass
                        if b'name="survey_technician"' in part:
                            try:
                                _, v_body = part.split(b'\r\n\r\n', 1)
                                survey_tech = v_body.decode('utf-8', errors='ignore').split('\r\n')[0].strip()
                            except Exception: pass
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
                        self._send_json({"error": "Failed to receive uploaded file"}, status=400)
                        return

                    CURRENT_PARCELS = enrich_parcels_with_security_tokens(read_survey_file(saved_path), system_officer=sys_officer, survey_technician=survey_tech)
                    CURRENT_SURVEY_FILE_PATH = saved_path
                    CURRENT_SURVEY_FILENAME = orig_filename
                    self._send_json({
                        "success": True,
                        "filename": orig_filename,
                        "total": len(CURRENT_PARCELS),
                        "parcels": CURRENT_PARCELS,
                        "official_centers": list_all_centers()
                    })

                elif 'application/json' in content_type:
                    body = self.rfile.read(content_length).decode('utf-8')
                    req_data = json.loads(body)
                    fpath = req_data.get('file_path')
                    if not fpath or not os.path.exists(fpath):
                        self._send_json({"error": "File path does not exist"}, status=400)
                        return
                    CURRENT_PARCELS = enrich_parcels_with_security_tokens(read_survey_file(fpath))
                    CURRENT_SURVEY_FILE_PATH = fpath
                    CURRENT_SURVEY_FILENAME = os.path.basename(fpath)
                    self._send_json({
                        "success": True,
                        "filename": os.path.basename(fpath),
                        "total": len(CURRENT_PARCELS),
                        "parcels": CURRENT_PARCELS,
                        "official_centers": list_all_centers()
                    })
                else:
                    self._send_json({"error": "Unsupported upload format"}, status=400)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 3. Preview Satellite Imagery
        elif path == '/api/preview-satellite':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                p_idx = req_data.get('parcel_index', 0)

                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "No parcel available"}, status=400)
                    return

                parcel = CURRENT_PARCELS[p_idx]
                pid = parcel.get("parcel_id", "0")
                sat_name = f"sat_{pid}.jpg"
                sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)

                generate_satellite_image(parcel, sat_path)

                self._send_json({
                    "success": True,
                    "image_url": f"/temp_assets/{sat_name}?t={int(time.time())}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 4. Preview CAD Croquis
        elif path == '/api/preview-croquis':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                p_idx = req_data.get('parcel_index', 0)

                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "No parcel available"}, status=400)
                    return

                parcel = CURRENT_PARCELS[p_idx]
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

                # Extract and persist font sizes
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
                    security_token=parcel.get("security_token"),
                    font_size_pts=font_size_pts,
                    font_size_dims=font_size_dims,
                    font_size_text=font_size_text
                )

                sat_name = f"sat_{pid}.jpg"
                sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
                if not os.path.exists(sat_path):
                    generate_satellite_image(parcel, sat_path)

                self._send_json({
                    "success": True,
                    "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}",
                    "satellite_url": f"/temp_assets/{sat_name}?t={int(time.time())}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 5. Output Directory Management
        elif path == '/api/browse-output-dir':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                init_dir = req_data.get('initial_dir') or OUTPUT_DIR
                folder = open_folder_picker(init_dir)
                if folder:
                    OUTPUT_DIR = folder
                    os.makedirs(OUTPUT_DIR, exist_ok=True)
                    save_persistent_config("output_dir", OUTPUT_DIR)
                self._send_json({"folder_path": folder, "output_dir": OUTPUT_DIR})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif path == '/api/set-output-dir':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                new_dir = req_data.get('output_dir', '').strip()
                if not new_dir:
                    self._send_json({"error": "No output directory specified"}, status=400)
                    return
                os.makedirs(new_dir, exist_ok=True)
                OUTPUT_DIR = new_dir
                save_persistent_config("output_dir", OUTPUT_DIR)
                self._send_json({"success": True, "output_dir": OUTPUT_DIR})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 5.5 Update & Secure Center
        elif path == '/api/update-center':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                p_idx = req_data.get('parcel_index', 0)

                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "No parcel available to update center"}, status=400)
                    return

                parcel = CURRENT_PARCELS[p_idx]
                raw_choice = req_data.get('center_id')
                if raw_choice is None:
                    raw_choice = req_data.get('center_name', '')

                # Resolve
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
                    self._send_json({"error": "المركز المختار غير مسجل في القاموس الرسمي"}, status=400)
                    return

                survey_tech = req_data.get('survey_technician', '')
                sys_officer = req_data.get('system_officer', '')
                if survey_tech: parcel["survey_technician"] = survey_tech
                if sys_officer: parcel["system_officer"] = sys_officer

                parcel["district"] = canon_name
                parcel["district_id"] = cid
                parcel["district_matched"] = True
                new_token = generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
                parcel["security_token"] = new_token

                # Regenerate croquis image if cached to reflect verified token in watermark
                pid = parcel.get("parcel_id", "0")
                croq_name = f"croq_{pid}.png"
                croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
                generate_croquis_image(parcel, croq_path, security_token=new_token)

                self._send_json({
                    "success": True,
                    "district": canon_name,
                    "district_id": cid,
                    "district_matched": True,
                    "security_token": new_token,
                    "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 6. Export Complete Citizen Package (The 6 Deliverables: PDF HTML/Data + DOCX + JSON + 2 Images + Input File)
        elif path == '/api/export-package':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}

                p_idx = req_data.get('parcel_index', 0)
                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "No parcel available to export"}, status=400)
                    return

                parcel = CURRENT_PARCELS[p_idx]
                pid = parcel.get("parcel_id", "0")

                # Update parcel with latest edited data from studio
                citizen_name = req_data.get('applicant_name') or parcel.get("applicant_name", f"citizen_{pid}")
                district_name = req_data.get('district') or req_data.get('session_data', {}).get('district') or parcel.get("district", "")

                clean_name = re.sub(r'[\\/*?:"<>|]', '_', citizen_name.strip())
                clean_dist = re.sub(r'[\\/*?:"<>|]', '_', district_name.strip())

                # Standard filename pattern: [ClientName]-[Center]
                file_base_name = f"{clean_name}-{clean_dist}" if clean_dist else clean_name

                # Dedicated citizen subfolder inside OUTPUT_DIR named [Client]-[Center]
                citizen_dir = os.path.join(OUTPUT_DIR, file_base_name)
                os.makedirs(citizen_dir, exist_ok=True)

                # 1 & 2: Images (Croquis + Satellite)
                croq_target_path = os.path.join(citizen_dir, f"croquis_{clean_name}.png")
                sat_target_path = os.path.join(citizen_dir, f"satellite_{clean_name}.jpg")

                # If studio sent custom base64 images (after cropping/zooming)
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

                # Convert images to base64 for embedding directly inside the final session JSON
                croq_b64_embed = ""
                sat_b64_embed = ""
                if os.path.exists(croq_target_path):
                    with open(croq_target_path, 'rb') as f:
                        croq_b64_embed = "data:image/png;base64," + base64.b64encode(f.read()).decode('utf-8')
                if os.path.exists(sat_target_path):
                    with open(sat_target_path, 'rb') as f:
                        sat_b64_embed = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')

                # 3: Official Word Document (.docx) named [Client]-[Center].docx
                template_docx = os.path.join(APP_DIR, "شهادة.docx")
                docx_out_path = os.path.join(citizen_dir, f"{file_base_name}.docx")
                
                survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
                sys_officer = req_data.get('system_officer', 'شريف محمد')
                parcel["survey_technician"] = survey_tech
                parcel["system_officer"] = sys_officer

                # Ensure official token is logged with officer & technician
                if parcel.get("district_id") is not None:
                    cid = parcel.get("district_id")
                    new_token = generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
                    parcel["security_token"] = new_token

                generate_certificate_docx(
                    parcel=parcel,
                    croquis_img_path=croq_target_path,
                    satellite_img_path=sat_target_path,
                    output_docx_path=docx_out_path,
                    template_path=template_docx,
                    survey_tech=survey_tech,
                    sys_officer=sys_officer,
                    security_token=parcel.get("security_token")
                )

                # 4: Official PDF Document (.pdf) named [Client]-[Center].pdf
                pdf_out_path = os.path.join(citizen_dir, f"{file_base_name}.pdf")
                cert_html = req_data.get('certificate_html', '')
                pdf_created = False
                if cert_html:
                    pdf_created = export_certificate_pdf(cert_html, pdf_out_path)

                # 5: Full Session State File (.json) containing full base64 images
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

                # 6: Archive Original Survey Input File
                archived_survey_file = None
                if CURRENT_SURVEY_FILE_PATH and os.path.exists(CURRENT_SURVEY_FILE_PATH):
                    fname = CURRENT_SURVEY_FILENAME or os.path.basename(CURRENT_SURVEY_FILE_PATH)
                    target_survey_path = os.path.join(citizen_dir, fname)
                    shutil.copy2(CURRENT_SURVEY_FILE_PATH, target_survey_path)
                    archived_survey_file = fname

                self._send_json({
                    "success": True,
                    "citizen_name": clean_name,
                    "district": clean_dist,
                    "file_base_name": file_base_name,
                    "folder_path": citizen_dir,
                    "files": {
                        "pdf": f"{file_base_name}.pdf" if pdf_created else None,
                        "docx": f"{file_base_name}.docx",
                        "session_json": f"{file_base_name}_session.json",
                        "croquis": f"croquis_{clean_name}.png",
                        "satellite": f"satellite_{clean_name}.jpg",
                        "survey_input": archived_survey_file
                    }
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json({"error": str(e)}, status=500)

        # 7. Open Folder in Explorer
        elif path == '/api/open-folder':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                target = req_data.get('folder_path') or OUTPUT_DIR
                # Create the folder if it doesn't exist yet
                os.makedirs(target, exist_ok=True)
                os.startfile(target)
                self._send_json({"success": True})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 8. Confirm Certificate Issuance in Cloud
        elif path == '/api/confirm-issuance':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                token = req_data.get('token', '').strip()
                if not token:
                    self._send_json({"error": "الكود الأمني مطلوب للاعتماد"}, status=400)
                    return
                
                conf_res = confirm_cloud_issuance(token)
                self._send_json({
                    "success": True,
                    "token": token,
                    "confirmed_at": conf_res.get("confirmed_at", ""),
                    "message": "تم اعتماد الشهادة بنجاح وتسجيلها رسمي للطباعة"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 9. Save Default Settings (Layout Sliders & Text Customizations)
        elif path == '/api/save-defaults':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                with open(DEFAULTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(req_data, f, ensure_ascii=False, indent=2)
                self._send_json({"success": True, "message": "تم حفظ الإعدادات الافتراضية بنجاح"})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 10. Reset Default Settings
        elif path == '/api/reset-defaults':
            try:
                if os.path.exists(DEFAULTS_FILE):
                    os.remove(DEFAULTS_FILE)
                self._send_json({"success": True, "message": "تم استعادة الإعدادات الأصلية بنجاح"})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 11. Restore Session from JSON
        elif path == '/api/restore-session':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                parcel = req_data.get('parcel')
                if not parcel:
                    self._send_json({"error": "بيانات المعاملة غير متوفرة في ملف الجلسة"}, status=400)
                    return
                
                pid = parcel.get('parcel_id', '0')
                CURRENT_PARCELS = [parcel]
                
                # استعادة الصور في temp_assets إن وجدت base64 أو توليدها تلقائياً
                croq_name = f"croq_{pid}.png"
                croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
                croq_b64 = req_data.get('croquis_base64')
                if croq_b64 and isinstance(croq_b64, str) and len(croq_b64) > 50:
                    try:
                        c_raw = croq_b64.split(',', 1)[1] if ',' in croq_b64 else croq_b64
                        with open(croq_path, 'wb') as f:
                            f.write(base64.b64decode(c_raw))
                    except Exception as ce:
                        print(f"[!] Warning decoding croquis: {ce}")
                elif not os.path.exists(croq_path) and parcel.get('vertices'):
                    try:
                        generate_croquis_image(parcel, croq_path, security_token=parcel.get('security_token'))
                    except Exception as ge:
                        print(f"[!] Warning generating croquis: {ge}")
                        
                sat_name = f"sat_{pid}.jpg"
                sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
                sat_b64 = req_data.get('satellite_base64')
                if sat_b64 and isinstance(sat_b64, str) and len(sat_b64) > 50:
                    try:
                        s_raw = sat_b64.split(',', 1)[1] if ',' in sat_b64 else sat_b64
                        with open(sat_path, 'wb') as f:
                            f.write(base64.b64decode(s_raw))
                    except Exception as se:
                        print(f"[!] Warning decoding satellite: {se}")
                elif not os.path.exists(sat_path) and parcel.get('vertices'):
                    try:
                        generate_satellite_image(parcel, sat_path)
                    except Exception as se:
                        print(f"[!] Warning generating satellite: {se}")

                self._send_json({
                    "success": True,
                    "message": "تم استعادة الجلسة في السيرفر بنجاح",
                    "parcel": parcel,
                    "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}" if os.path.exists(croq_path) else None,
                    "satellite_url": f"/temp_assets/{sat_name}?t={int(time.time())}" if os.path.exists(sat_path) else None
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        else:
            self.send_error(404, "Not Found")

def kill_existing_on_port(port):
    """Try to kill any existing process listening on the given port (Windows only)."""
    try:
        import subprocess
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f"127.0.0.1:{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                try:
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True, timeout=5)
                    print(f"[INIT] Killed stale process PID {pid} on port {port}")
                except Exception:
                    pass
    except Exception:
        pass

def start_server(port=8765):
    # First, clean up any stale process holding our preferred port
    kill_existing_on_port(port)
    import time as _time
    _time.sleep(0.3)  # Short wait for OS to release the port

    for p in range(port, port + 20):
        try:
            server = HTTPServer(('127.0.0.1', p), DUDCV3RequestHandler)
            print(f"==================================================")
            print(f"  🏛️ DUDC V3.5 Cadastral Studio Server Running")
            print(f"  URL: http://127.0.0.1:{p}")
            print(f"==================================================")
            return server, p
        except OSError:
            continue
    raise RuntimeError("Could not find open port between 8765 and 8785")

if __name__ == '__main__':
    server, port = start_server(8765)
    url = f"http://127.0.0.1:{port}"
    print(f"[INFO] Opening browser: {url}")
    # Small delay to let server fully initialize before opening browser
    import threading
    def _open_browser():
        import time as _t
        _t.sleep(0.8)
        webbrowser.open(url)
    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DUDC V3.5 Server...")
        server.server_close()

