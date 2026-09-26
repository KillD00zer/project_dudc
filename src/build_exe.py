"""
PyInstaller Build Script for Cadastral Survey Certificate Generator
==================================================================
Compiles the complete system into a standalone Windows executable and
updates project_dudc_ V2 distribution folder automatically.
"""

import os
import subprocess
import sys
import shutil

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
V2_DIR = os.path.join(PROJECT_ROOT, "project_dudc_ V2")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--name", "Certificate_Generator",
    "--add-data", f"{os.path.join(BASE_DIR, 'شهادة.docx')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'Google Maps Satellite.lyr')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'ف.xls')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'index.html')};.",
    "--add-data", f"{os.path.join(BASE_DIR, 'core')};core",
    "--hidden-import", "openpyxl",
    "--hidden-import", "xlrd",
    "--hidden-import", "pyproj",
    "--hidden-import", "shapely",
    "--hidden-import", "PIL",
    "--hidden-import", "matplotlib",
    "--hidden-import", "docx",
    "--hidden-import", "cryptography",
    "--hidden-import", "security_overlay",
    "--hidden-import", "encoder_api",
    "--hidden-import", "arabic_reshaper",
    "--hidden-import", "bidi",
    "--hidden-import", "bidi.algorithm",
    os.path.join(BASE_DIR, "app_server.py")
]

print("Running PyInstaller to compile V2 with Anti-Forgery & Watermark...")
res = subprocess.run(cmd, cwd=BASE_DIR)

if res.returncode == 0:
    dist_folder = os.path.join(BASE_DIR, "dist", "Certificate_Generator")
    print(f"\n[SUCCESS] Build succeeded at: {dist_folder}")
    
    # Copy new Certificate_Generator.exe and updated assets into project_dudc_ V2
    if os.path.exists(V2_DIR):
        print(f"Deploying updated build directly into: {V2_DIR} ...")
        # Copy exe
        src_exe = os.path.join(dist_folder, "Certificate_Generator.exe")
        dst_exe = os.path.join(V2_DIR, "Certificate_Generator.exe")
        shutil.copy2(src_exe, dst_exe)
        
        # Copy _internal contents
        src_internal = os.path.join(dist_folder, "_internal")
        dst_internal = os.path.join(V2_DIR, "_internal")
        if os.path.exists(src_internal):
            for item in os.listdir(src_internal):
                s = os.path.join(src_internal, item)
                d = os.path.join(dst_internal, item)
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
        print("[SUCCESS] project_dudc_ V2 is now 100% updated with the new binary and security features!")
else:
    print(f"\n[ERROR] Build failed with return code {res.returncode}")
