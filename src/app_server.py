"""
Cadastral Survey Certificate System - Local Web Server & API Controller
========================================================================
Provides lightweight local REST endpoints for the simplified non-programmer UI:
- GET  /                  : Serves the clean 3-step English web interface (index.html).
- POST /api/load-sample   : Loads the built-in sample file 'ف.xls'.
- POST /api/upload        : Uploads and parses user's CSV / XLS file.
- POST /api/set-output-dir: Sets the user's chosen output directory.
- GET  /api/get-output-dir: Returns the current output directory path.
- POST /api/generate      : Synthesizes Google Satellite map, CAD croquis, and publishes DOCX.
- POST /api/open-folder   : Opens the generated certificates folder in Windows Explorer.
"""

import os
import sys
import re
import json
import shutil
import tempfile
import webbrowser
import base64
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from geo_engine import read_survey_file
from satellite_engine import generate_satellite_image
from croquis_engine import generate_croquis_image
from docx_builder import generate_certificate_docx
from encoder_api import generate_dudc_token
from datetime import datetime

# When packaged with PyInstaller --onedir, sys.executable is inside the app folder (e.g., project_dudc/Certificate_Generator.exe)
# sys._MEIPASS is inside _internal. We want assets from _internal or app_dir, but OUTPUT_DIR strictly next to the executable!
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    BUNDLE_DIR = getattr(sys, '_MEIPASS', APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR

# OUTPUT_DIR is always created in APP_DIR (next to Certificate_Generator.exe, NEVER in _internal!)

CONFIG_FILE = os.path.join(APP_DIR, "app_config.json")

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

def open_folder_picker(initial_dir=""):
    """
    Open Windows native folder selection dialog and return absolute path.
    """
    init_dir = initial_dir if (initial_dir and os.path.exists(initial_dir)) else (OUTPUT_DIR if os.path.exists(OUTPUT_DIR) else os.getcwd())

    # Method 1: Tkinter filedialog (Modern Windows native folder dialog)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        root.focus_force()
        folder = filedialog.askdirectory(
            title="اختر مجلد حفظ الشهادات المساحية",
            initialdir=init_dir
        )
        root.destroy()
        if folder:
            return os.path.normpath(folder)
    except Exception:
        pass

    # Method 2: PowerShell Windows Forms FolderBrowserDialog fallback
    try:
        import subprocess
        ps_cmd = (
            "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
            "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$f.Description = 'اختر مجلد حفظ الشهادات المساحية'; "
            f"$f.SelectedPath = '{init_dir}'; "
            "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }"
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=120)
        out = res.stdout.strip()
        if out and os.path.exists(out):
            return os.path.normpath(out)
    except Exception:
        pass

    return ""

_saved_cfg = load_saved_config()
OUTPUT_DIR = _saved_cfg.get("output_dir") or os.path.join(APP_DIR, "generated_certificates")
TEMP_ASSETS_DIR = os.path.join(APP_DIR, "temp_assets")

def resolve_asset(filename):
    """Find asset first next to executable, then in internal bundle."""
    p_app = os.path.join(APP_DIR, filename)
    if os.path.exists(p_app):
        return p_app
    p_bundle = os.path.join(BUNDLE_DIR, filename)
    if os.path.exists(p_bundle):
        return p_bundle
    return p_app

SAMPLE_FILE = resolve_asset("ف.xls")
INDEX_HTML = resolve_asset("index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_ASSETS_DIR, exist_ok=True)

# Global in-memory cache of current loaded parcels and input survey file
CURRENT_PARCELS = []
CURRENT_SURVEY_FILE_PATH = None
CURRENT_SURVEY_FILENAME = None

import docx_builder

def enrich_parcels_with_security_tokens(parcels):
    now_dt = datetime.now()
    date_display, _ = docx_builder.format_issue_date(now_dt)
    for p in parcels:
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

        try:
            token = generate_dudc_token(
                name=p.get("applicant_name", ""),
                lon=p1_lon,
                lat=p1_lat,
                lon_2=p2_lon,
                lat_2=p2_lat,
                receipt_1=r1,
                receipt_2=r2,
                center=p.get("district", ""),
                date_val=now_dt
            )
        except Exception as e:
            print(f"[!] Warning: Token error during enrich: {e}")
            token = None

        p["security_token"] = token
        p["issue_date_display"] = date_display
    return parcels

class CadastralRequestHandler(BaseHTTPRequestHandler):
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
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        global OUTPUT_DIR
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path in ('/', '/index.html'):
            self._send_file(INDEX_HTML, 'text/html; charset=utf-8')
        elif path == '/api/get-output-dir':
            self._send_json({"output_dir": OUTPUT_DIR})
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
                CURRENT_PARCELS = enrich_parcels_with_security_tokens(read_survey_file(SAMPLE_FILE))
                CURRENT_SURVEY_FILE_PATH = SAMPLE_FILE
                CURRENT_SURVEY_FILENAME = "ف.xls"
                self._send_json({
                    "success": True,
                    "filename": "ف.xls",
                    "total": len(CURRENT_PARCELS),
                    "parcels": CURRENT_PARCELS
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                
        # 2. Upload Custom File (Multipart or raw file)
        elif path == '/api/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                content_type = self.headers.get('Content-Type', '')
                
                # Check for file path in json payload
                if 'application/json' in content_type:
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
                        "parcels": CURRENT_PARCELS
                    })
                    return
                    
                # Multipart form upload
                if 'multipart/form-data' in content_type:
                    raw_data = self.rfile.read(content_length)
                    # Simple boundary extraction
                    boundary = content_type.split("boundary=")[-1].encode('ascii')
                    parts = raw_data.split(b'--' + boundary)
                    
                    saved_path = None
                    file_name = "uploaded_survey.xls"
                    for part in parts:
                        if b'filename=' in part:
                            # Extract filename
                            header, body = part.split(b'\r\n\r\n', 1)
                            body = body.rstrip(b'\r\n--')
                            
                            for line in header.decode('latin1', errors='ignore').split('\r\n'):
                                if 'filename=' in line:
                                    fname_match = line.split('filename=')[-1].strip('"\'')
                                    if fname_match:
                                        file_name = fname_match
                                        
                            ext = os.path.splitext(file_name)[1]
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                            temp_file.write(body)
                            temp_file.close()
                            saved_path = temp_file.name
                            break
                            
                    if not saved_path:
                        self._send_json({"error": "No file uploaded"}, status=400)
                        return
                        
                    CURRENT_PARCELS = enrich_parcels_with_security_tokens(read_survey_file(saved_path))
                    CURRENT_SURVEY_FILE_PATH = saved_path
                    CURRENT_SURVEY_FILENAME = file_name
                    self._send_json({
                        "success": True,
                        "filename": file_name,
                        "total": len(CURRENT_PARCELS),
                        "parcels": CURRENT_PARCELS
                    })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 3. Generate Visual Assets: Satellite Only
        elif path == '/api/preview-satellite':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                p_idx = req_data.get('parcel_index', 0)
                
                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "Invalid parcel index"}, status=400)
                    return
                    
                parcel = CURRENT_PARCELS[p_idx]
                pid = parcel.get("parcel_id", "0")
                
                sat_name = f"sat_{pid}.jpg"
                sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
                
                generate_satellite_image(parcel, sat_path)
                
                self._send_json({
                    "success": True,
                    "satellite_url": f"/temp_assets/{sat_name}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 3b. Generate / Update CAD Croquis with interactive boundary inputs
        elif path == '/api/preview-croquis' or path == '/api/preview':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                p_idx = req_data.get('parcel_index', 0)
                
                if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                    self._send_json({"error": "Invalid parcel index"}, status=400)
                    return
                    
                parcel = CURRENT_PARCELS[p_idx]
                pid = parcel.get("parcel_id", "0")
                
                # Apply any interactive boundaries sent from the UI
                if "boundaries" in req_data:
                    parcel["boundaries"] = req_data["boundaries"]
                    
                # Apply any interactive segment lengths sent from the UI table
                if "edited_lengths" in req_data:
                    edited_lens = req_data["edited_lengths"]
                    for i, l_val in enumerate(edited_lens):
                        if i < len(parcel.get("segments", [])):
                            try:
                                parcel["segments"][i]["length_m"] = round(float(l_val), 2)
                            except (ValueError, TypeError):
                                pass
                                
                # Apply any interactive segment directions sent from the UI table
                if "edited_directions" in req_data:
                    edited_dirs = req_data["edited_directions"]
                    for i, d_val in enumerate(edited_dirs):
                        if i < len(parcel.get("segments", [])):
                            parcel["segments"][i]["direction"] = d_val
                            
                # Apply structured edited_segments if present
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
                    
                croq_name = f"croq_{pid}.png"
                croq_path = os.path.join(TEMP_ASSETS_DIR, croq_name)
                
                generate_croquis_image(parcel, croq_path, security_token=parcel.get("security_token"))
                
                # Also ensure satellite exists for backwards compatibility
                sat_name = f"sat_{pid}.jpg"
                sat_path = os.path.join(TEMP_ASSETS_DIR, sat_name)
                if not os.path.exists(sat_path):
                    generate_satellite_image(parcel, sat_path)
                
                self._send_json({
                    "success": True,
                    "croquis_url": f"/temp_assets/{croq_name}",
                    "satellite_url": f"/temp_assets/{sat_name}"
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 4. Upload Custom Satellite or CAD Croquis Image
        elif path == '/api/upload-image':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                content_type = self.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    body = self.rfile.read(content_length).decode('utf-8')
                    req_data = json.loads(body)
                    img_type = req_data.get('type', 'satellite') # 'satellite' or 'croquis'
                    img_b64 = req_data.get('image_base64', '')
                    p_idx = req_data.get('parcel_index', 0)
                    
                    if not CURRENT_PARCELS or p_idx >= len(CURRENT_PARCELS):
                        self._send_json({"error": "No parcel loaded"}, status=400)
                        return
                        
                    parcel = CURRENT_PARCELS[p_idx]
                    pid = parcel.get("parcel_id", "0")
                    
                    if ',' in img_b64:
                        img_b64 = img_b64.split(',', 1)[1]
                    raw_bytes = base64.b64decode(img_b64)
                    
                    if img_type == 'satellite':
                        fname = f"sat_{pid}.jpg"
                        out_path = os.path.join(TEMP_ASSETS_DIR, fname)
                        with open(out_path, 'wb') as f:
                            f.write(raw_bytes)
                        parcel['custom_satellite_path'] = out_path
                        self._send_json({
                            "success": True,
                            "type": "satellite",
                            "url": f"/temp_assets/{fname}?t={int(time.time())}"
                        })
                    else:
                        fname = f"croq_{pid}.png"
                        out_path = os.path.join(TEMP_ASSETS_DIR, fname)
                        with open(out_path, 'wb') as f:
                            f.write(raw_bytes)
                        parcel['custom_croquis_path'] = out_path
                        self._send_json({
                            "success": True,
                            "type": "croquis",
                            "url": f"/temp_assets/{fname}?t={int(time.time())}"
                        })
                    return
                else:
                    self._send_json({"error": "Unsupported content type, expected JSON"}, status=400)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 5. Set Output Directory
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

        # 6. Generate Final DOCX Certificates (per-folder output)
        elif path == '/api/generate':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode('utf-8')
                req_data = json.loads(body) if length > 0 else {}
                
                edited_boundaries = req_data.get('edited_boundaries', {})
                edited_lengths = req_data.get('edited_lengths', {})
                edited_directions = req_data.get('edited_directions', {})
                edited_segments = req_data.get('edited_segments', {})
                survey_tech = req_data.get('survey_technician', 'محمد ابراهيم بدير')
                sys_officer = req_data.get('system_officer', 'شريف محمد')
                
                if not CURRENT_PARCELS:
                    self._send_json({"error": "No parcels loaded to generate!"}, status=400)
                    return
                    
                generated_files = []
                for idx, parcel in enumerate(CURRENT_PARCELS):
                    pid = parcel.get("parcel_id", str(idx))
                    
                    # Apply any edited boundary descriptions from the UI
                    if pid in edited_boundaries:
                        parcel["boundaries"] = edited_boundaries[pid]
                        
                    # Apply any edited segment lengths from the UI
                    lens_list = edited_lengths.get(str(pid)) or edited_lengths.get(pid)
                    if not lens_list and isinstance(edited_lengths, list):
                        lens_list = edited_lengths
                    if lens_list:
                        for i, l_val in enumerate(lens_list):
                            if i < len(parcel.get("segments", [])):
                                try:
                                    parcel["segments"][i]["length_m"] = round(float(l_val), 2)
                                except (ValueError, TypeError):
                                    pass
                                    
                    # Apply any edited segment directions from the UI
                    dirs_list = edited_directions.get(str(pid)) or edited_directions.get(pid)
                    if not dirs_list and isinstance(edited_directions, list):
                        dirs_list = edited_directions
                    if dirs_list:
                        for i, d_val in enumerate(dirs_list):
                            if i < len(parcel.get("segments", [])):
                                parcel["segments"][i]["direction"] = d_val
                                
                    # Apply structured edited_segments from the UI
                    segs_list = edited_segments.get(str(pid)) or edited_segments.get(pid)
                    if not segs_list and isinstance(edited_segments, list):
                        segs_list = edited_segments
                    if segs_list:
                        for i, s_data in enumerate(segs_list):
                            if i < len(parcel.get("segments", [])):
                                if "length_m" in s_data:
                                    try:
                                        parcel["segments"][i]["length_m"] = round(float(s_data["length_m"]), 2)
                                    except (ValueError, TypeError):
                                        pass
                                if "direction" in s_data:
                                    parcel["segments"][i]["direction"] = s_data["direction"]
                        
                    # Create per-certificate subfolder named after the applicant
                    clean_name = re.sub(r'[\\/*?:"<>|]', '_', parcel.get("applicant_name", f"parcel_{pid}"))
                    cert_folder = os.path.join(OUTPUT_DIR, clean_name)
                    os.makedirs(cert_folder, exist_ok=True)
                    
                    # Target image paths inside the certificate folder
                    sat_path = os.path.join(cert_folder, f"satellite_{clean_name}.jpg")
                    croq_path = os.path.join(cert_folder, f"croquis_{clean_name}.png")
                    out_docx_path = os.path.join(cert_folder, f"{clean_name}.docx")
                    
                    # Compute DUDC Security Token (Two points P1 & P2 + Exact Arabic + Receipts)
                    verts = parcel.get("vertices", [])
                    p1_lon = verts[0]["lon"] if verts else 31.381790
                    p1_lat = verts[0]["lat"] if verts else 31.051135
                    p2_lon = verts[1]["lon"] if len(verts) > 1 else p1_lon
                    p2_lat = verts[1]["lat"] if len(verts) > 1 else p1_lat

                    rcp_raw = str(parcel.get("receipt_no", "0")).replace(" ", "")
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

                    now_dt = datetime.now()
                    try:
                        security_token = generate_dudc_token(
                            name=parcel.get("applicant_name", ""),
                            lon=p1_lon,
                            lat=p1_lat,
                            lon_2=p2_lon,
                            lat_2=p2_lat,
                            receipt_1=r1,
                            receipt_2=r2,
                            center=parcel.get("district", ""),
                            date_val=now_dt
                        )
                    except Exception as e:
                        print(f"[!] Warning: Token generation error: {e}")
                        security_token = None

                    parcel["security_token"] = security_token

                    # If user uploaded a custom satellite image, copy it; otherwise generate it
                    if parcel.get('custom_satellite_path') and os.path.exists(parcel['custom_satellite_path']):
                        shutil.copy2(parcel['custom_satellite_path'], sat_path)
                    else:
                        generate_satellite_image(parcel, sat_path)
                        
                    # If user uploaded a custom CAD croquis drawing, copy it; otherwise generate it
                    if parcel.get('custom_croquis_path') and os.path.exists(parcel['custom_croquis_path']):
                        shutil.copy2(parcel['custom_croquis_path'], croq_path)
                    else:
                        generate_croquis_image(parcel, croq_path, security_token=security_token)
                        
                    generate_certificate_docx(parcel, croq_path, sat_path, out_docx_path, survey_tech=survey_tech, sys_officer=sys_officer, issue_date_val=now_dt, security_token=security_token)
                    
                    # Copy input survey file (Excel/CSV) into citizen's folder
                    if CURRENT_SURVEY_FILE_PATH and os.path.exists(CURRENT_SURVEY_FILE_PATH):
                        dest_survey_file = os.path.join(cert_folder, CURRENT_SURVEY_FILENAME or "survey_input.xls")
                        try:
                            shutil.copy2(CURRENT_SURVEY_FILE_PATH, dest_survey_file)
                        except Exception as e:
                            print(f"[!] Warning: Could not copy survey file to {dest_survey_file}: {e}")
                    
                    generated_files.append({
                        "applicant_name": parcel.get("applicant_name"),
                        "filename": f"{clean_name}.docx",
                        "folder": cert_folder,
                        "path": out_docx_path
                    })
                    
                # Also copy input survey file directly to top-level output directory
                if CURRENT_SURVEY_FILE_PATH and os.path.exists(CURRENT_SURVEY_FILE_PATH):
                    top_survey_file = os.path.join(OUTPUT_DIR, CURRENT_SURVEY_FILENAME or "survey_input.xls")
                    try:
                        shutil.copy2(CURRENT_SURVEY_FILE_PATH, top_survey_file)
                    except Exception as e:
                        print(f"[!] Warning: Could not copy survey file to {top_survey_file}: {e}")
                
                self._send_json({
                    "success": True,
                    "count": len(generated_files),
                    "output_dir": OUTPUT_DIR,
                    "files": generated_files
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        # 6. Open Output Folder in Windows Explorer
        elif path == '/api/open-folder':
            try:
                if sys.platform == 'win32':
                    os.startfile(OUTPUT_DIR)
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open', OUTPUT_DIR])
                self._send_json({"success": True, "output_dir": OUTPUT_DIR})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Unknown API route")

def start_server(port=8765, open_browser=True):
    server = HTTPServer(('127.0.0.1', port), CadastralRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f" Cadastral Survey Certificate System Running!")
    print(f" Web Interface: {url}")
    print(f" Output Folder: {OUTPUT_DIR}")
    print(" Press Ctrl+C to stop.")
    print("=" * 60)
    
    if open_browser:
        webbrowser.open(url)
        
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == '__main__':
    port = 8765
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    start_server(port=port, open_browser=True)
