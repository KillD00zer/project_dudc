"""
Server Configuration & System Directory Helpers (Enhanced Edition)
==================================================================
Handles configuration persistence, Windows Desktop detection, output directory
validation, multi-drive discovery, in-app visual directory browsing, and resilient native pickers.
"""

import os
import sys
import json
import base64
import string
import threading
import subprocess
from typing import Dict, Any, List, Optional, Tuple

_folder_picker_lock = threading.Lock()

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(APP_DIR, "app_config.json")
DEFAULTS_FILE = os.path.join(APP_DIR, "user_default_settings.json")
DRAFTS_DIR = os.path.join(APP_DIR, "drafts")
TEMP_ASSETS_DIR = os.path.join(APP_DIR, "temp_assets")
ASSETS_DIR = os.path.join(APP_DIR, "assets")
SAMPLE_FILE = os.path.join(APP_DIR, "ف.xls")
INDEX_HTML = os.path.join(APP_DIR, "index.html")

os.makedirs(DRAFTS_DIR, exist_ok=True)
os.makedirs(TEMP_ASSETS_DIR, exist_ok=True)


def load_saved_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_persistent_config(key: str, val: Any) -> None:
    cfg = load_saved_config()
    cfg[key] = val
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_safe_default_output_dir() -> str:
    """
    Dynamically finds the Desktop path for the current logged-in user on Windows:
    1. Checks OneDrive Desktop
    2. Checks standard User Home Desktop
    3. Fallback: <APP_DIR>/generated_certificates
    """
    try:
        for od_var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
            od_path = os.environ.get(od_var)
            if od_path and os.path.isdir(od_path):
                candidate = os.path.join(od_path, "Desktop")
                if os.path.isdir(candidate):
                    return os.path.normpath(candidate)

        user_home = os.path.expanduser("~")
        candidate = os.path.join(user_home, "Desktop")
        if os.path.isdir(candidate):
            return os.path.normpath(candidate)
    except Exception:
        pass

    fallback = os.path.join(APP_DIR, "generated_certificates")
    try:
        os.makedirs(fallback, exist_ok=True)
    except Exception:
        pass
    return os.path.normpath(fallback)


def get_system_drives() -> List[Dict[str, str]]:
    """Returns list of available drives on Windows (e.g. C:, D:)."""
    drives = []
    try:
        from ctypes import windll
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drv = f"{letter}:\\"
                if os.path.exists(drv):
                    drives.append({
                        "path": os.path.normpath(drv),
                        "label": f"القرص ({letter}:)",
                        "icon": "💽"
                    })
            bitmask >>= 1
    except Exception:
        for letter in ("C", "D", "E", "F"):
            drv = f"{letter}:\\"
            if os.path.exists(drv):
                drives.append({
                    "path": os.path.normpath(drv),
                    "label": f"القرص ({letter}:)",
                    "icon": "💽"
                })
    return drives


def get_quick_locations() -> List[Dict[str, str]]:
    """Returns quick location shortcuts (Desktop, Documents, Downloads, App Out)."""
    locs = []
    user_home = os.path.expanduser("~")

    # 1. Desktop
    desktop = get_safe_default_output_dir()
    if os.path.isdir(desktop):
        locs.append({
            "id": "desktop",
            "name": "سطح المكتب",
            "icon": "🖥️",
            "path": desktop
        })

    # 2. Documents
    docs = None
    for od_var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        od_path = os.environ.get(od_var)
        if od_path and os.path.isdir(od_path):
            cand = os.path.join(od_path, "Documents")
            if os.path.isdir(cand):
                docs = cand
                break
    if not docs:
        cand = os.path.join(user_home, "Documents")
        if os.path.isdir(cand):
            docs = cand

    if docs:
        locs.append({
            "id": "documents",
            "name": "المستندات",
            "icon": "📁",
            "path": os.path.normpath(docs)
        })

    # 3. Downloads
    downloads = os.path.join(user_home, "Downloads")
    if os.path.isdir(downloads):
        locs.append({
            "id": "downloads",
            "name": "التنزيلات",
            "icon": "📥",
            "path": os.path.normpath(downloads)
        })

    # 4. App Directory Default
    app_out = os.path.join(APP_DIR, "generated_certificates")
    os.makedirs(app_out, exist_ok=True)
    locs.append({
        "id": "app_default",
        "name": "مجلد المنظومة الداخلي",
        "icon": "🏛️",
        "path": os.path.normpath(app_out)
    })

    return locs


def list_subdirectories(raw_path: str) -> Dict[str, Any]:
    """
    Safely lists all child subdirectories in a directory for the in-app visual explorer.
    Does not require any shell or PowerShell invocation.
    """
    if not raw_path or not isinstance(raw_path, str) or not raw_path.strip():
        raw_path = get_safe_default_output_dir()

    target = os.path.normpath(raw_path.strip())
    if not os.path.exists(target):
        target = get_safe_default_output_dir()

    if not os.path.isdir(target):
        parent = os.path.dirname(target)
        target = parent if (parent and os.path.isdir(parent)) else get_safe_default_output_dir()

    can_write = False
    try:
        test_file = os.path.join(target, f".perm_{os.getpid()}.tmp")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        can_write = True
    except Exception:
        can_write = False

    subdirs = []
    try:
        for entry in os.scandir(target):
            try:
                if entry.is_dir(follow_symlinks=False):
                    name = entry.name
                    # Ignore hidden / system folders
                    if not name.startswith('$') and not name.startswith('.') and name.lower() not in ('system volume information', 'recovery', '$recycle.bin'):
                        subdirs.append({
                            "name": name,
                            "path": os.path.normpath(entry.path)
                        })
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError) as e:
        return {
            "success": False,
            "error": f"لا تتوفر صلاحية تصفح هذا المجلد: {e}",
            "current_path": target,
            "can_write": can_write,
            "subdirectories": []
        }

    subdirs.sort(key=lambda x: x["name"].lower())

    parent_path = os.path.dirname(target)
    has_parent = bool(parent_path and os.path.isdir(parent_path) and parent_path != target)

    return {
        "success": True,
        "current_path": target,
        "parent_path": parent_path if has_parent else None,
        "can_write": can_write,
        "subdirectories": subdirs
    }


def create_subdirectory(parent_path: str, folder_name: str) -> Dict[str, Any]:
    """Creates a new folder inside parent_path."""
    if not parent_path or not os.path.isdir(parent_path):
        return {"success": False, "error": "المجلد الرئيسي غير موجود"}

    clean_name = "".join(c for c in folder_name if c not in r'\/:*?"<>|').strip()
    if not clean_name:
        return {"success": False, "error": "اسم المجلد غير صالح أو يحتوي على أحرف محظورة"}

    new_dir = os.path.join(parent_path, clean_name)
    try:
        os.makedirs(new_dir, exist_ok=True)
        return {
            "success": True,
            "folder_path": os.path.normpath(new_dir),
            "folder_name": clean_name
        }
    except Exception as e:
        return {"success": False, "error": f"فشل إنشاء المجلد: {e}"}


def validate_path_status(raw_dir: str) -> Dict[str, Any]:
    """Checks validity and write permissions of a given path string."""
    if not raw_dir or not isinstance(raw_dir, str) or not raw_dir.strip():
        default_dir = get_safe_default_output_dir()
        return {
            "valid": True,
            "exists": True,
            "can_write": True,
            "can_create": False,
            "path": default_dir,
            "message": "تم ضبط المسار على سطح المكتب الافتراضي"
        }

    candidate = os.path.normpath(raw_dir.strip())
    if "?" in candidate:
        return {
            "valid": False,
            "exists": False,
            "can_write": False,
            "can_create": False,
            "path": candidate,
            "message": "المسار يحتوي على رموز غير مدعومة أو علامات استفهام"
        }

    if os.path.isdir(candidate):
        try:
            test_file = os.path.join(candidate, f".perm_{os.getpid()}.tmp")
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
            return {
                "valid": True,
                "exists": True,
                "can_write": True,
                "can_create": False,
                "path": candidate,
                "message": "المجلد موجود وقابل للكتابة وحفظ الشهادات"
            }
        except Exception:
            return {
                "valid": True,
                "exists": True,
                "can_write": False,
                "can_create": False,
                "path": candidate,
                "message": "المجلد موجود لكن لا تتوفر صلاحية الكتابة فيه"
            }

    # Check if parent exists so it can be created
    parent = os.path.dirname(candidate)
    if parent and os.path.isdir(parent):
        return {
            "valid": True,
            "exists": False,
            "can_write": True,
            "can_create": True,
            "path": candidate,
            "message": "المجلد غير موجود حالياً وسيتم إنشاؤه تلقائياً عند حفظ الشهادة"
        }

    return {
        "valid": False,
        "exists": False,
        "can_write": False,
        "can_create": False,
        "path": candidate,
        "message": "المسار غير صالح أو القرص المحدد غير متصل بهذا الجهاز"
    }


def validate_or_fallback_output_dir(raw_dir: Optional[str]) -> str:
    status = validate_path_status(raw_dir or "")
    if status.get("valid") and (status.get("exists") or status.get("can_write")):
        return status["path"]
    return get_safe_default_output_dir()


def open_folder_picker(initial_dir: str = "", current_output_dir: str = "") -> str:
    """
    Open Windows folder picker with multi-tier fallback:
    1. Tkinter filedialog (Instant, native, zero-PowerShell, no console window)
    2. PowerShell TopMost FolderBrowserDialog (Clean fallback if Tkinter missing)
    """
    if not _folder_picker_lock.acquire(blocking=False):
        return ""
    try:
        init_dir = (
            initial_dir
            if (initial_dir and os.path.exists(initial_dir))
            else (current_output_dir if (current_output_dir and os.path.exists(current_output_dir)) else get_safe_default_output_dir())
        )

        # 1. Try Tkinter (Instant, no cmd / shell / PowerShell window)
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            root.focus_force()
            selected = filedialog.askdirectory(
                initialdir=init_dir,
                title="اختر مجلد حفظ الشهادات المساحية",
                mustexist=False
            )
            root.destroy()
            if selected and os.path.isdir(selected):
                return os.path.normpath(selected)
        except Exception as te:
            print(f"[!] Tkinter picker notice: {te}, falling back to PowerShell TopMost")

        # 2. Try PowerShell with TopMost window (prevents opening behind browser)
        try:
            init_b64 = base64.b64encode(init_dir.encode("utf-8")).decode("ascii")
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$d = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$d.ShowNewFolderButton = $true; "
                "try { $d.UseDescriptionForTitle = $true } catch {}; "
                "$d.Description = 'اختر مجلد حفظ الشهادات المساحية'; "
                f"$initBytes = [Convert]::FromBase64String('{init_b64}'); "
                "$initPath = [System.Text.Encoding]::UTF8.GetString($initBytes); "
                "if (Test-Path -Path $initPath) { $d.SelectedPath = $initPath }; "
                "$form = New-Object System.Windows.Forms.Form; "
                "$form.TopMost = $true; "
                "if ($d.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) { "
                "  $outBytes = [System.Text.Encoding]::UTF8.GetBytes($d.SelectedPath); "
                "  [Console]::WriteLine([Convert]::ToBase64String($outBytes)) "
                "}"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
                capture_output=True, text=True, timeout=45
            )
            raw_out = res.stdout.strip()
            if raw_out:
                decoded_path = base64.b64decode(raw_out).decode("utf-8", errors="replace").strip()
                if decoded_path and "?" not in decoded_path and os.path.isdir(decoded_path):
                    return os.path.normpath(decoded_path)
        except Exception as pe:
            print(f"[!] PowerShell picker exception: {pe}")

        return ""
    finally:
        _folder_picker_lock.release()
