---
title: Session Manager (session_manager.py)
tags: [backend, state, session, thread-safety, recovery]
related_files:
  - DUDC V3/server/session_manager.py
---

# ⚙️ Session Manager (`session_manager.py`)

File: [`DUDC V3/server/session_manager.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/session_manager.py)

Manages in-memory active parcels, output directories, and session recovery snapshots using synchronization locks.

---

## 🔒 The `SessionManager` Singleton

The server maintains a global instance:
```python
SESSION_MANAGER = SessionManager()
```

### State Fields
- `_lock: threading.Lock` - Concurrency mutex.
- `current_parcels: List[Dict[str, Any]]` - Parsed survey parcels.
- `current_survey_file_path: Optional[str]` - Path of the currently ingested survey file.
- `current_survey_filename: Optional[str]` - Base name of the survey file.
- `active_session: Dict[str, Any]` - Comprehensive session state (parcel data, layout spacing, text customization, image transforms).
- `output_dir: str` - Current validated directory for saving outputs.

---

## 💾 Real-Time Disk Snapshotting (`active_session.json`)

To prevent loss of work if the browser is closed or the server restarts unexpectedly, `update_active_session()` automatically writes a recovery snapshot:
- Destination: `DUDC V3/temp_assets/active_session.json`
- Base64 optimization: Croquis and satellite images are written directly to `temp_assets/croq_0.png` and `temp_assets/sat_0.jpg`, while the snapshot JSON references their local URLs to keep file operations lightweight.
- Upon client startup, the frontend calls `/api/get-active-session` and can seamlessly restore unsaved work.

---

## 🧹 Session & Image Cache Purging (`clear_session_cache`)
When a surveyor starts a fresh import:
- Resets `current_parcels`, survey file paths, and active session.
- Purges stale runtime images (`croq_*.png`, `sat_*.jpg`, `temp_print_*.html`) from `temp_assets/`.
- Prevents image mixing between consecutive client certificates.

