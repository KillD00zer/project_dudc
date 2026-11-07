---
title: Drafts Drawer & Auto-Save (drafts.js)
tags: [frontend, drafts, autosave, recovery]
related_files:
  - DUDC V3/js/drafts.js
  - DUDC V3/server/drafts_service.py
---

# 💻 Drafts Drawer & Auto-Save (`drafts.js`)

File: [`DUDC V3/js/drafts.js`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/js/drafts.js)

Provides auto-save scheduling, draft management drawer, snapshot restorations, and offline recovery.

---

## ⏱️ Auto-Save Loop
- An internal timer (`scheduleDraftAutoSave()`) triggers every **45 seconds** if changes have been made in the studio.
- Automatically sends a lightweight synchronization payload to `/api/sync-session`.
- Serializes full draft snapshots to `/api/save-draft` whenever a user navigates between stages.

---

## 📂 Draft Management Drawer
Surveyors can click the **"📁 مسودات اليوم"** button in the header bar to open a slide-out drawer:
- Queries `/api/list-drafts` to show all saved certificates.
- Displays applicant name, center name, area, and save timestamp.
- Actions per draft:
  - **استعادة (Restore):** Calls `/api/load-draft`, unpacks images to `temp_assets/`, restores parcel coordinates, text styles, and switches directly to Stage 2.
  - **حذف (Delete):** Calls `/api/delete-draft` with confirmation.

