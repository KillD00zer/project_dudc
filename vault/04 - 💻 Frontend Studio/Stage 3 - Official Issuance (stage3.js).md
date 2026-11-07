---
title: Stage 3 - Official Issuance (stage3.js)
tags: [frontend, stage3, issuance, export, print]
related_files:
  - DUDC V3/js/stage3.js
  - DUDC V3/server/handlers.py
---

# 💻 Stage 3 - Official Issuance (`stage3.js`)

File: [`DUDC V3/js/stage3.js`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/js/stage3.js)

Manages cloud certification, official token confirmation, document package export, and printing.

---

## 🔒 Security Gate & Printing Constraint

To prevent the generation of unverified certificates:
- The print button is strictly disabled (`disabled = true`) until the package has been officially exported and verified (`hasSavedCurrentPackage === true`).
- If a user attempts to force print via `Ctrl+P`, the stylesheet hides the document and alerts the user to complete official export first.

---

## 📦 Package Export Trigger (`/api/export-package`)

When the surveyor clicks **"اعتماد وتصدير الشهادة"**:
1. Extracts complete HTML snapshot of `#certificateSheet` via `buildStandaloneCertificateHtml()`.
2. Packages the active session, including applicant details, coordinates, base64 images, and typography configurations.
3. Sends POST request to `/api/export-package`.
4. Server generates:
   - Vector PDF via Headless Microsoft Edge.
   - Comprehensive JSON session file.
   - Standalone Croquis PNG and Satellite JPG.
   - Copies original input survey file.
5. On completion, updates UI with green confirmation card showing:
   - Output directory path.
   - Generated files list.
   - 1-Click button: **"📂 فتح مجلد الشهادة في ويندوز"** (`/api/open-folder`).
   - Unlocks the **"🖨️ طباعة الشهادة"** button.

