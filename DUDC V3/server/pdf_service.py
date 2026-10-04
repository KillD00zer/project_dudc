"""
Headless Edge Vector PDF Exporter
=================================
Automates Microsoft Edge to render HTML certificates to crisp, vector A4 PDF.
"""

import os
import time
import subprocess
from .config import TEMP_ASSETS_DIR


def export_certificate_pdf(cert_html: str, output_pdf_path: str) -> bool:
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
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
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
