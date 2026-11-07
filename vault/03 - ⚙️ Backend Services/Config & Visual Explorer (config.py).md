---
title: Config & Visual Explorer (config.py)
tags: [backend, config, filesystem, visual-explorer, drives]
related_files:
  - DUDC V3/server/config.py
  - tests/test_folder_explorer.py
---

# ⚙️ Config & Visual Explorer (`config.py`)

File: [`DUDC V3/server/config.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/config.py)

Handles persistent application settings, Windows Desktop path resolution, multi-drive discovery, native folder pickers, and the backend engine for the **In-App Visual Directory Explorer**.

---

## 🖥️ Dynamic Windows Desktop & Folder Discovery

Surveyors often have varied Windows account setups (e.g. OneDrive Desktop synchronization vs. Local Desktop).
`get_safe_default_output_dir()` implements an intelligent search cascade:
1. **OneDrive Desktop:** Checks environment variables `OneDrive`, `OneDriveCommercial`, and `OneDriveConsumer`.
2. **Standard User Home:** Checks `os.path.expanduser("~")/Desktop`.
3. **Internal Safe Fallback:** `<APP_DIR>/generated_certificates`.

---

## 📂 In-App Visual Explorer Backend (`os.scandir`)

To eliminate reliance on PowerShell or system shell dialogues (which frequently freeze or get hidden behind full-screen browser windows), `config.py` provides pure Python directory traversal:

### Key Functions
- `get_system_drives() -> List[Dict]`: Uses `ctypes.windll.kernel32.GetLogicalDrives()` to detect all available physical and network drives (`C:\`, `D:\`, `E:\`, etc.).
- `get_quick_locations() -> List[Dict]`: Returns 1-click shortcuts for Desktop, Documents, Downloads, and internal App folder.
- `list_subdirectories(raw_path: str) -> Dict[str, Any]`:
  - Uses `os.scandir(target)` to list child folders without touching PowerShell.
  - Automatically filters out hidden and OS system folders (`$Recycle.Bin`, `System Volume Information`, `.git`).
  - Performs live write-permission test by attempting to write a temporary token file `.perm_<pid>.tmp`.
  - Returns `can_write: bool` and alphabetical folder listing.
- `create_subdirectory(parent_path: str, folder_name: str) -> Dict[str, Any]`:
  - Sanitizes forbidden Windows filename characters (`\/:*?"<>|`).
  - Creates the new folder using `os.makedirs(..., exist_ok=True)`.

---

## 🪟 Fallback Native Windows Folder Pickers

If the user clicks the "🪟 ويندوز" button, `open_folder_picker()` executes a two-tier fallback:
1. **Tkinter Dialog (Instant):** Uses `tkinter.filedialog.askdirectory` with `-topmost` flag. Zero PowerShell invocation.
2. **PowerShell TopMost Dialog:** If Tkinter is unavailable, launches a hidden PowerShell command passing `System.Windows.Forms.FolderBrowserDialog` with `TopMost = $true` to ensure the window never opens hidden behind the browser.

