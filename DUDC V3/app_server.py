"""
DUDC V3.5 - Next-Generation Cadastral Certificate Workflow Server
================================================================
Dakahlia Utility Data Center (مركز معلومات شبكات المرافق)
Provides local REST API endpoints for the complete 3-Stage Workflow:
1. Stage 1: Survey Ingestion, Geodesic Validation, Satellite & Croquis Generation, Token Creation
2. Stage 2: Studio Edit, Contextual Typography, Image Crop & Zoom, Watermark Control
3. Stage 3: Direct Vector A4 PDF Print & Complete Citizen Package Export (PDF + JSON + Images + Survey File)
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
import uuid
try:
    from http.server import ThreadingHTTPServer as ServerClass, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer as ServerClass, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime

# Local core engines
from geo_engine import read_survey_file
from satellite_engine import generate_satellite_image
from croquis_engine import generate_croquis_image
from encoder_api import generate_dudc_token, confirm_cloud_issuance
from centers import resolve_center, get_center_name, list_all_centers

ARABIC_DAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

def to_arabic_numerals(text):
    if text is None:
        return ""
    trans = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return str(text).translate(trans)

def format_issue_date(issue_date_val=None):
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
    date_str = to_arabic_numerals(f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}")
    display_text = f"تحريراً في : {day_name} الموافق {date_str}"
    iso_date = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"
    return display_text, iso_date

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "app_config.json")
DEFAULTS_FILE = os.path.join(APP_DIR, "user_default_settings.json")
DRAFTS_DIR = os.path.join(APP_DIR, "drafts")
os.makedirs(DRAFTS_DIR, exist_ok=True)
TRIAL_TOKEN = "DUDC-TRIAL-SAMPLE-PREVIEW-000000-000000"

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
        else:
            p["district"] = raw_dist

        # Official security token generation is delayed until Stage 3 verification with final edited data
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

def ensure_base64_image(img_input, img_type='croquis', parcel=None, pid='0'):
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

    # Check default temp asset name
    if not target_disk_path:
        cand = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png" if img_type == "croquis" else f"sat_{pid}.jpg")
        if os.path.exists(cand) and os.path.getsize(cand) > 0:
            target_disk_path = cand

    # Read from disk if found
    if target_disk_path and os.path.exists(target_disk_path):
        try:
            mime = "image/png" if target_disk_path.lower().endswith(".png") else "image/jpeg"
            with open(target_disk_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
        except Exception as e:
            print(f"[!] Warning reading image {target_disk_path}: {e}")

    # Generate from parcel geometry if available
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

    # Fallback to sample asset
    sample = os.path.join(ASSETS_DIR, "sample_croquis.png" if img_type == "croquis" else "sample_satellite.jpg")
    if os.path.exists(sample):
        mime = "image/png" if sample.lower().endswith(".png") else "image/jpeg"
        with open(sample, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"

    return ""

class DUDCV3RequestHandler(BaseHTTPRequestHandler):
    def address_string(self):
        # Override to prevent reverse DNS lookup on Windows (eliminates 2.0s delay per request)
        return self.client_address[0]

    def log_message(self, format, *args):
        # High performance logger without reverse DNS
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.client_address[0]} - {format % args}\n")
    def _send_json(self, data, status=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def _send_file(self, file_path, content_type='text/html; charset=utf-8'):
        if not os.path.exists(file_path):
            try:
                self.send_error(404, "File not found")
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
                pass
            return
        with open(file_path, 'rb') as f:
            content = f.read()
        try:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            pass

    def do_GET(self):
        global OUTPUT_DIR
        host = self.headers.get('Host', '')
        if host.startswith('localhost'):
            port_str = f":{self.server.server_port}" if getattr(self.server, 'server_port', 8765) != 80 else ""
            self.send_response(301)
            self.send_header('Location', f"http://127.0.0.1{port_str}{self.path}")
            self.end_headers()
            return

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
        elif path == '/api/list-drafts':
            try:
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
                self._send_json({"success": True, "drafts": drafts, "count": len(drafts)})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
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
                    security_token=parcel.get("security_token") or TRIAL_TOKEN,
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

        # 4.5 Upload Custom Parcel Image (Croquis or Satellite) from User Device
        elif path == '/api/upload-parcel-image':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}

                target_type = req_data.get('type', 'croquis')
                b64_data = req_data.get('image_base64', '')
                p_idx = req_data.get('parcel_index', 0)

                pid = "0"
                if CURRENT_PARCELS and p_idx < len(CURRENT_PARCELS):
                    pid = CURRENT_PARCELS[p_idx].get("parcel_id", "0")

                if b64_data and 'data:' in b64_data and ',' in b64_data:
                    img_bytes = base64.b64decode(b64_data.split(',', 1)[1])
                    if target_type == 'croquis':
                        out_path = os.path.join(TEMP_ASSETS_DIR, f"croq_{pid}.png")
                    else:
                        out_path = os.path.join(TEMP_ASSETS_DIR, f"sat_{pid}.jpg")
                    with open(out_path, 'wb') as f:
                        f.write(img_bytes)
                    self._send_json({"success": True, "saved_path": out_path})
                else:
                    self._send_json({"error": "Invalid base64 image data"}, status=400)
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
                # Delay official token creation to Stage 3 verification
                parcel["security_token"] = None

                # Generate croquis preview image with trial watermark
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

                self._send_json({
                    "success": True,
                    "district": canon_name,
                    "district_id": cid,
                    "district_matched": True,
                    "security_token": None,
                    "trial_token": TRIAL_TOKEN,
                    "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 6. Export Complete Citizen Package (Deliverables: Vector PDF + JSON + 2 Images + Survey Input File)
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

                # 3: Ensure official security token is preserved or generated safely
                survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
                sys_officer = req_data.get('system_officer', 'شريف محمد')
                parcel["survey_technician"] = survey_tech
                parcel["system_officer"] = sys_officer

                existing_token = parcel.get("security_token") or req_data.get('session_data', {}).get('security_token') or req_data.get('security_token')
                if not existing_token and parcel.get("district_id") is not None:
                    try:
                        cid = parcel.get("district_id")
                        existing_token = generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
                    except Exception as te:
                        print(f"[!] Warning: Token error during export (using fallback): {te}")
                        existing_token = f"DUDC-{int(time.time())}"

                if existing_token:
                    parcel["security_token"] = existing_token

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

                # 7: Auto-remove draft associated with this session if exists
                try:
                    target_draft_id = req_data.get('draft_id') or req_data.get('session_data', {}).get('draft_id')
                    if target_draft_id:
                        fid = target_draft_id if target_draft_id.startswith("draft_") else f"draft_{target_draft_id}"
                        dpath = os.path.join(DRAFTS_DIR, f"{fid}.json")
                        if os.path.exists(dpath):
                            os.remove(dpath)
                            print(f"[Drafts] Auto-deleted draft {fid} after package export.")
                    if os.path.exists(DRAFTS_DIR):
                        for df in os.listdir(DRAFTS_DIR):
                            if df.endswith('.json'):
                                f_full = os.path.join(DRAFTS_DIR, df)
                                try:
                                    with open(f_full, 'r', encoding='utf-8') as f:
                                        cd = json.load(f)
                                    c_name = str(cd.get('applicant_name') or cd.get('parcel', {}).get('applicant_name', '')).strip()
                                    if c_name and c_name == clean_name:
                                        os.remove(f_full)
                                        print(f"[Drafts] Auto-cleared matched draft {df} for {clean_name}")
                                        break
                                except Exception:
                                    pass
                except Exception as de:
                    print(f"[!] Warning deleting draft on export: {de}")

                self._send_json({
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

        # 8. Generate and Confirm Official Security Token with Final Edited Data (Stage 3 Verification)
        elif path == '/api/confirm-issuance':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}

                p_idx = req_data.get('parcel_index', 0)
                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    if req_data.get('parcel') and isinstance(req_data['parcel'], dict):
                        CURRENT_PARCELS = [req_data['parcel']]
                        parcel = CURRENT_PARCELS[0]
                    else:
                        self._send_json({"error": "لا توجد قطعة مساحية نشطة للاعتماد"}, status=400)
                        return
                else:
                    parcel = CURRENT_PARCELS[p_idx]

                # Update parcel with latest edited data from studio before generating code
                if req_data.get('applicant_name'):
                    parcel["applicant_name"] = req_data['applicant_name'].strip()
                if req_data.get('national_id'):
                    parcel["national_id"] = req_data['national_id'].strip()
                if req_data.get('receipt_no'):
                    parcel["receipt_no"] = req_data['receipt_no'].strip()
                if req_data.get('district'):
                    raw_d = req_data['district'].strip()
                    is_m, cid_res, cname = resolve_center(raw_d)
                    if is_m:
                        parcel["district"] = cname
                        parcel["district_id"] = cid_res
                        parcel["district_matched"] = True
                if req_data.get('village'):
                    parcel["village"] = req_data['village'].strip()
                if req_data.get('address'):
                    parcel["address"] = req_data['address'].strip()
                if req_data.get('order_no'):
                    parcel["order_no"] = req_data['order_no'].strip()
                    parcel["request_no"] = req_data['order_no'].strip()
                if req_data.get('deal_type'):
                    parcel["deal_type"] = req_data['deal_type'].strip()
                    parcel["transaction_type"] = req_data['deal_type'].strip()
                if req_data.get('site_desc'):
                    parcel["site_desc"] = req_data['site_desc'].strip()
                    parcel["site_status"] = req_data['site_desc'].strip()
                if req_data.get('survey_technician'):
                    parcel["survey_technician"] = req_data['survey_technician'].strip()
                if req_data.get('system_officer'):
                    parcel["system_officer"] = req_data['system_officer'].strip()

                CURRENT_PARCELS[p_idx] = parcel

                cid = parcel.get("district_id")
                if cid is None:
                    is_m, cid_res, cname = resolve_center(parcel.get("district", "المنصورة"))
                    cid = cid_res if is_m else 0
                    if is_m: parcel["district"] = cname

                sys_officer = parcel.get("system_officer", "شريف محمد")
                survey_tech = parcel.get("survey_technician", "محمد ابراهيم بدير")

                # Generate authentic official token using final confirmed data
                official_token = generate_token_for_parcel(parcel, cid, system_officer=sys_officer, survey_technician=survey_tech)
                parcel["security_token"] = official_token

                # Confirm in cloud audit registry
                conf_res = confirm_cloud_issuance(official_token)
                if not conf_res.get("success"):
                    raise RuntimeError(conf_res.get("error", "فشل توثيق الشهادة في السجل السحابي الرسمي"))

                # Regenerate croquis
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

                # Auto-sync draft file on disk if draft_id is provided
                draft_id = req_data.get('draft_id')
                if draft_id:
                    file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
                    draft_file = os.path.join(DRAFTS_DIR, f"{file_id}.json")
                    if os.path.exists(draft_file):
                        try:
                            with open(draft_file, 'r', encoding='utf-8') as df:
                                ddata = json.load(df)
                            ddata["security_token"] = official_token
                            ddata["applicant_name"] = parcel.get("applicant_name", ddata.get("applicant_name"))
                            ddata["district"] = parcel.get("district", ddata.get("district"))
                            ddata["saved_at"] = datetime.now().strftime("%Y/%m/%d %I:%M %p")
                            ddata["parcel"] = parcel
                            if "session_data" in ddata and isinstance(ddata["session_data"], dict):
                                ddata["session_data"]["security_token"] = official_token
                                ddata["session_data"]["parcel"] = parcel
                                ddata["session_data"]["applicant_name"] = parcel.get("applicant_name")
                                ddata["session_data"]["district"] = parcel.get("district")
                                ddata["session_data"]["national_id"] = parcel.get("national_id")
                                ddata["session_data"]["receipt_no"] = parcel.get("receipt_no")
                                ddata["session_data"]["village"] = parcel.get("village")
                                ddata["session_data"]["address"] = parcel.get("address")
                                ddata["session_data"]["order_no"] = parcel.get("order_no")
                                ddata["session_data"]["deal_type"] = parcel.get("deal_type")
                                ddata["session_data"]["site_desc"] = parcel.get("site_desc")
                                ddata["session_data"]["survey_technician"] = parcel.get("survey_technician")
                                ddata["session_data"]["system_officer"] = parcel.get("system_officer")
                            with open(draft_file, 'w', encoding='utf-8') as df:
                                json.dump(ddata, df, ensure_ascii=False, indent=2)
                        except Exception as de:
                            print(f"[!] Warning updating draft on token confirmation: {de}")

                self._send_json({
                    "success": True,
                    "token": official_token,
                    "confirmed_at": conf_res.get("confirmed_at", datetime.now().strftime("%Y/%m/%d %H:%M:%S")),
                    "croquis_url": f"/temp_assets/{croq_name}?t={int(time.time())}",
                    "message": "تم إصدار وتوثيق كود الأمان الرسمي بنجاح في السجل السحابي"
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
                if croq_b64 and isinstance(croq_b64, str) and 'data:image' in croq_b64:
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
                if sat_b64 and isinstance(sat_b64, str) and 'data:image' in sat_b64:
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
                import traceback
                print(f"[!] Error in restore-session: {e}")
                traceback.print_exc()
                self._send_json({"error": str(e)}, status=500)

        # 12. Save Certificate Draft
        elif path == '/api/save-draft':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}

                draft_id = req_data.get('draft_id')
                if not draft_id:
                    draft_id = f"draft_{int(time.time())}_{uuid.uuid4().hex[:6]}"
                
                file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
                draft_filename = f"{file_id}.json"
                draft_path = os.path.join(DRAFTS_DIR, draft_filename)

                # Add metadata
                req_data["draft_id"] = file_id
                req_data["saved_at"] = datetime.now().strftime("%Y/%m/%d %I:%M %p")
                
                p = req_data.get("parcel") or req_data.get("session_data", {}).get("parcel", {})
                pid = p.get('parcel_id', '0') if isinstance(p, dict) else '0'
                if p and isinstance(p, dict) and p.get('applicant_name'):
                    CURRENT_PARCELS = [p]

                # Convert both croquis and satellite images to guaranteed Base64 strings
                raw_croq = req_data.get("croquis_base64") or req_data.get("session_data", {}).get("croquis_base64")
                raw_sat = req_data.get("satellite_base64") or req_data.get("session_data", {}).get("satellite_base64")

                croq_b64 = ensure_base64_image(raw_croq, "croquis", parcel=p, pid=pid)
                sat_b64 = ensure_base64_image(raw_sat, "satellite", parcel=p, pid=pid)

                # Embed in all relevant places in the draft JSON
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

                req_data["applicant_name"] = req_data.get("applicant_name") or p.get("applicant_name") or "بدون اسم"
                req_data["district"] = req_data.get("district") or p.get("district") or "غير محدد"
                req_data["area"] = req_data.get("area") or p.get("contract_area_text") or "--"

                with open(draft_path, "w", encoding="utf-8") as f:
                    json.dump(req_data, f, ensure_ascii=False, indent=2)

                self._send_json({
                    "success": True,
                    "draft_id": file_id,
                    "saved_at": req_data["saved_at"],
                    "message": "تم حفظ المسودة بنجاح في صندوق مسودات اليوم"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 13. Load Certificate Draft
        elif path == '/api/load-draft':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                draft_id = req_data.get('draft_id', '').strip()
                if not draft_id:
                    self._send_json({"error": "معرف المسودة مطلوب"}, status=400)
                    return
                
                file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
                draft_path = os.path.join(DRAFTS_DIR, f"{file_id}.json")
                if not os.path.exists(draft_path):
                    self._send_json({"error": "المسودة غير موجودة أو تم حذفها"}, status=404)
                    return
                
                with open(draft_path, "r", encoding="utf-8") as f:
                    draft_data = json.load(f)

                # Sync into server state
                p = draft_data.get("parcel") or draft_data.get("session_data", {}).get("parcel")
                croq_url = None
                sat_url = None
                if p and isinstance(p, dict):
                    CURRENT_PARCELS = [p]
                    pid = p.get('parcel_id', '0')
                    
                    # Unpack images into temp_assets if present
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

                self._send_json({
                    "success": True,
                    "draft_id": file_id,
                    "draft": draft_data,
                    "croquis_url": croq_url,
                    "satellite_url": sat_url
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 14. Delete Certificate Draft
        elif path == '/api/delete-draft':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
                req_data = json.loads(body) if body else {}
                draft_id = req_data.get('draft_id', '').strip()
                if not draft_id:
                    self._send_json({"error": "معرف المسودة مطلوب للحذف"}, status=400)
                    return
                
                file_id = draft_id if draft_id.startswith("draft_") else f"draft_{draft_id}"
                draft_path = os.path.join(DRAFTS_DIR, f"{file_id}.json")
                if os.path.exists(draft_path):
                    os.remove(draft_path)
                    self._send_json({"success": True, "message": "تم حذف المسودة بنجاح"})
                else:
                    self._send_json({"success": True, "message": "المسودة غير موجودة بالفعل"})
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
            server = ServerClass(('127.0.0.1', p), DUDCV3RequestHandler)
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

