---
title: REST API Catalog (handlers.py)
tags: [backend, api, endpoints, rest, contracts]
related_files:
  - DUDC V3/server/handlers.py
  - tests/test_endpoints.py
---

# ⚙️ REST API Catalog (`handlers.py`)

File: [`DUDC V3/server/handlers.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/handlers.py)

Contains the complete routing table for all GET and POST HTTP endpoints.

---

## 📥 GET Endpoints

| Endpoint | Purpose | Response Payload / Behavior |
|---|---|---|
| `/` or `/index.html` | Serves main UI document | `text/html; charset=utf-8` |
| `/api/health` | Service heartbeat & latency check | `{"status": "online", "version": "4.0", "timestamp": float}` |
| `/api/check-update` | Checks GitHub origin/main for incoming commits | `{"success": bool, "update_available": bool, "commits": [...]}` |
| `/api/get-active-session` | Retrieves active in-memory session | `{"success": true, "active_session": {...}}` |
| `/api/get-output-dir` | Returns currently selected output directory | `{"output_dir": "C:\\Users\\...\\Desktop"}` |
| `/api/quick-locations` | Enumerates Windows drives & shortcut folders | `{"locations": [...], "drives": [...], "current_output_dir": "..."}` |
| `/api/get-defaults` | Fetches persisted user styling defaults | `{"success": bool, "defaults": {...}}` |
| `/api/get-centers` | Returns the 18 official Dakahlia centers | `{"centers": [[0, "المنصورة"], ...]}` |
| `/api/list-drafts` | Lists all saved JSON drafts in `drafts/` | `{"success": true, "drafts": [...], "count": int}` |
| `/api/download-survey-csv` | Directly downloads active standardized survey CSV | `text/csv; charset=utf-8-sig` attachment |
| `/css/*` | Serves modular CSS style sheets | `text/css; charset=utf-8` |
| `/js/*` | Serves modular JavaScript files | `application/javascript; charset=utf-8` |
| `/assets/*` | Serves static assets, icons, logos | Image MIME types (`image/png`, `image/jpeg`, `image/x-icon`) |
| `/temp_assets/*` | Serves runtime rendered Croquis / Satellite images | Image MIME types with `no-cache` headers |

---

## 📤 POST Endpoints

| Endpoint | Description | Request Body (JSON / Multipart) | Key Output |
|---|---|---|---|
| `/api/upload` | Ingests Excel (`.xls`, `.xlsx`) or `.csv` survey file | Multipart form data (file) or JSON `{use_sample: true}` | Parsed parcel list with calculated areas, segments, and validation statuses |
| `/api/upload-docx` | Ingests Word cadastral certificate (`.docx`), synthesizes standard CSV, saves permanently to disk, and ingests into engine | Multipart form data (`.docx` file + officers) | Parcel list, `saved_csv_path`, `csv_filename`, and auto-previews |
| `/api/preview-satellite` | Re-generates satellite imagery for a parcel | `{parcel_index: 0, stated_area_m2: float}` | `{"success": true, "satellite_url": "/temp_assets/sat_0.jpg?t=..."}` |
| `/api/preview-croquis` | Re-generates CAD Croquis image with custom fonts | `{parcel_index: 0, font_size_pts: 16, font_size_dims: 16, ...}` | `{"success": true, "croquis_url": "/temp_assets/croq_0.png?t=..."}` |
| `/api/upload-parcel-image` | Uploads user-provided custom Croquis or Satellite image | `{parcel_index: 0, image_type: "croquis"\|"satellite", image_base64: "..."}` | Overwrites asset in `temp_assets/` and parcel memory |
| `/api/browse-output-dir` | Spawns native Windows folder dialog | `{initial_dir: "..."}` | `{"folder_path": "D:\\Work\\..."}` |
| `/api/browse-directory` | Traverses directories for in-app visual explorer | `{directory_path: "..."}` | Subdirectory tree with write-permission check |
| `/api/create-directory` | Creates a new subdirectory | `{parent_path: "...", folder_name: "..."}` | `{"success": true, "folder_path": "..."}` |
| `/api/validate-path` | Validates path existence and write permissions | `{path: "..."}` | `{"valid": bool, "can_write": bool, "message": "..."}` |
| `/api/set-output-dir` | Updates and persists output destination | `{output_dir: "..."}` | `{"success": true, "output_dir": "..."}` |
| `/api/update-center` | Updates selected center/district for parcel | `{parcel_index: 0, center_id: int}` | Updated parcel with matched canonical district |
| `/api/export-package` | Exports complete citizen package (PDF, JSON, PNG, JPG) | `{parcel_index: 0, certificate_html: "...", session_data: {...}}` | Creates `[Citizen]-[District]` folder with vector PDF and session JSON |
| `/api/open-folder` | Opens citizen folder in Windows Explorer | `{folder_path: "..."}` | Launches `explorer.exe` |
| `/api/confirm-issuance` | Verifies and logs issuance in central Modal ledger | `{token: "...", parcel_index: 0, ...}` | Verified official token status |
| `/api/save-defaults` | Saves user typography & spacing preferences | `{defaults: {...}}` | Written to `user_default_settings.json` |
| `/api/reset-defaults` | Resets settings to factory defaults | None | Clears `user_default_settings.json` |
| `/api/sync-session` | Synchronizes frontend state into server memory | `{session_data: {...}}` | Updates `SESSION_MANAGER` & `active_session.json` |
| `/api/restore-session` | Reloads last active session after browser crash | None | Returns recovered parcel and settings |
| `/api/save-draft` | Persists working draft with embedded base64 | `{draft_id: "...", session_data: {...}}` | Written to `drafts/draft_<id>.json` |
| `/api/load-draft` | Unpacks draft and extracts images to disk | `{draft_id: "..."}` | Unpacks images to `temp_assets/` and restores state |
| `/api/delete-draft` | Deletes a draft from disk | `{draft_id: "..."}` | Removes file from `drafts/` |
| `/api/perform-update` | Triggers git pull and updates local repo | None | Pulls latest code from GitHub |

