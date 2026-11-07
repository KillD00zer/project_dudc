---
title: Drafts Service (drafts_service.py)
tags: [backend, drafts, persistence, base64, autosave]
related_files:
  - DUDC V3/server/drafts_service.py
  - DUDC V3/js/drafts.js
---

# ⚙️ Drafts Service (`drafts_service.py`)

File: [`DUDC V3/server/drafts_service.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/drafts_service.py)

Manages saving, loading, listing, and cleaning temporary certificate drafts stored in `DUDC V3/drafts/`.

---

## 📦 Self-Contained Draft Architecture (Embedded Base64)

A persistent issue in older document generation tools was broken relative links when restoring drafts (e.g. temporary images deleted from `temp_assets/`).
`drafts_service.py` ensures all drafts are **100% self-contained**:

```python
def ensure_base64_image(img_input, img_type='croquis', parcel=None, pid='0') -> str:
    # 1. If already valid data:image/...;base64, return as-is
    # 2. If disk path or temp URL, read binary and convert to base64
    # 3. If image missing but parcel geometry exists, trigger on-the-fly regeneration
    # 4. Fallback to sample placeholder
```

### Advantages
- The JSON draft file in `drafts/draft_<id>.json` contains all parcel data, custom text formatting, coordinates, and complete base64 image strings.
- Can be transferred between computers or archived permanently without loss of images.

---

## 🗃️ Key Functions
- `list_drafts() -> List[Dict]`: Scans `drafts/`, extracts applicant name, district, area, and timestamp, returning drafts sorted reverse-chronologically.
- `save_draft(req_data: Dict) -> Dict`: Generates unique ID (`draft_<timestamp>_<uuid>`), embeds base64 graphics, and writes indented UTF-8 JSON.
- `load_draft(draft_id: str) -> Dict`: Reads the JSON file and unpacks base64 graphics into `temp_assets/croq_<pid>.png` and `temp_assets/sat_<pid>.jpg` so the frontend can preview them immediately.
- `delete_draft(draft_id: str) -> Dict`: Removes the draft file when manually deleted or automatically when officially exported.

