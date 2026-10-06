"""
DUDC V4.0 - Next-Generation Cadastral Certificate Workflow Server
================================================================
Dakahlia Utility Data Center (مركز معلومات شبكات المرافق)
Refactored Modular Application Server.
"""

import sys
import os

# Ensure the application root is always in sys.path (required for portable/embedded runtimes)
_app_dir = os.path.dirname(os.path.abspath(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import json
import webbrowser
import threading
import subprocess
import time

try:
    from http.server import ThreadingHTTPServer as ServerClass, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer as ServerClass, BaseHTTPRequestHandler

# Import modular components
from server.config import (
    APP_DIR,
    INDEX_HTML,
    SAMPLE_FILE,
    DEFAULTS_FILE,
    DRAFTS_DIR,
    TEMP_ASSETS_DIR,
    ASSETS_DIR,
    open_folder_picker,
    load_saved_config,
    save_persistent_config,
    validate_or_fallback_output_dir,
    get_safe_default_output_dir,
)
from server.pdf_service import export_certificate_pdf
from server.git_service import check_git_updates, perform_git_update
from server.drafts_service import list_drafts, save_draft, load_draft, delete_draft, ensure_base64_image
from server.session_manager import (
    SESSION_MANAGER,
    format_issue_date,
    to_arabic_numerals,
    to_english_numerals,
)
from server.handlers import handle_get, handle_post

# Backward compatibility module attributes
OUTPUT_DIR = SESSION_MANAGER.output_dir
CURRENT_PARCELS = SESSION_MANAGER.current_parcels


class DUDCV3RequestHandler(BaseHTTPRequestHandler):
    def address_string(self):
        # Override to prevent reverse DNS lookup on Windows (eliminates 2.0s delay per request)
        return self.client_address[0]

    def log_message(self, format, *args):
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
        host = self.headers.get('Host', '')
        if host.startswith('localhost'):
            port_str = f":{self.server.server_port}" if getattr(self.server, 'server_port', 8765) != 80 else ""
            self.send_response(301)
            self.send_header('Location', f"http://127.0.0.1{port_str}{self.path}")
            self.end_headers()
            return

        handled = handle_get(self, self.path)
        if not handled:
            self.send_error(404, "Not Found")

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(length) if length > 0 else b""
        handled = handle_post(self, self.path, body_bytes)
        if not handled:
            self.send_error(404, "Not Found")


def kill_existing_on_port(port: int = 8765):
    """Try to kill any existing process listening on the given port (Windows only)."""
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f"127.0.0.1:{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                try:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=5)
                    print(f"[INIT] Killed stale process PID {pid} on port {port}")
                except Exception:
                    pass
    except Exception:
        pass


def start_server(port: int = 8765):
    kill_existing_on_port(port)
    time.sleep(0.3)

    for p in range(port, port + 20):
        try:
            server = ServerClass(('127.0.0.1', p), DUDCV3RequestHandler)
            print(f"==================================================")
            print(f"  🏛️ DUDC V4.0 Cadastral Studio Server Running")
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

    def _open_browser():
        time.sleep(0.8)
        webbrowser.open(url)

    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DUDC V4.0 Server...")
        server.server_close()
