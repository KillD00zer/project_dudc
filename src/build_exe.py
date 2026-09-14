"""
PyInstaller Build Script for Cadastral Survey Certificate Generator
==================================================================
Compiles the complete system into a standalone Windows executable.
"""

import os
import subprocess
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--name", "Certificate_Generator",
    "--add-data", f"{os.path.join(BASE_DIR, 'شهادة.docx')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'Google Maps Satellite.lyr')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'ف.xls')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'index.html')};.",
    "--hidden-import", "openpyxl",
    "--hidden-import", "xlrd",
    "--hidden-import", "pyproj",
    "--hidden-import", "shapely",
    "--hidden-import", "PIL",
    "--hidden-import", "matplotlib",
    "--hidden-import", "docx",
    os.path.join(BASE_DIR, "app_server.py")
]

print("Running PyInstaller...")
res = subprocess.run(cmd, cwd=BASE_DIR)
if res.returncode == 0:
    print("\n[SUCCESS] Build succeeded! Output located in: dist/Certificate_Generator/")
else:
    print(f"\n[ERROR] Build failed with return code {res.returncode}")
