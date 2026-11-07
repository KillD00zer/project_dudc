---
title: Strict System Invariants
tags: [invariants, rules, standards, architecture]
type: rules
last_updated: 2026-11-07
---

# 🛡️ Strict System Invariants (The 10 Golden Rules)

Every developer and AI agent working on DUDC V4.0 must adhere strictly to these 10 non-negotiable rules. Violating any of them breaks system compliance or corrupts official records.

---

### Rule 1: Legal Tolerance Limit ($\pm 2.00\text{ m}^2$)
The legal discrepancy threshold between stated area and geodesic WGS84 calculated area is strictly $\mathbf{\pm 2.00\text{ m}^2}$.
- $|\Delta| \le 2.00 \implies \text{PASS}$
- $|\Delta| > 2.00 \implies \text{MANUAL\_REVISION}$
Never relax or alter this threshold unless explicitly mandated by official decree.

### Rule 2: Citizen Output Naming Standard
Every client package folder and all exported files MUST follow the strict pattern:
$$\mathbf{[اسم\ العميل]-[المركز]}$$
*Example:*
- Folder: `أحمد محمد إبراهيم-طلخا/`
- PDF: `أحمد محمد إبراهيم-طلخا.pdf`
- Session: `أحمد محمد إبراهيم-طلخا_session.json`
- Croquis: `croquis_أحمد محمد إبراهيم.png`
- Satellite: `satellite_أحمد محمد إبراهيم.jpg`

### Rule 3: Missing Data Stringent Fallback
If National ID, Receipt Number, or Request Number are blank, zero, or missing from the survey file:
- **Mandatory Output:** The Arabic string **"لا يوجد بيانات متاحة"** MUST be displayed.
- **Prohibited:** Never fill with dummy data, placeholder zeros, `None`, or English strings like "N/A".

### Rule 4: Image Upload Button Visibility Boundary
Custom image upload buttons (for croquis and satellite images) are permitted **EXCLUSIVELY in Stage 1**.
- They MUST be completely absent from Stage 2 (Studio) and Stage 3 to preserve a clean, printable document.

### Rule 5: Pure Base64 Draft & Session Self-Containment
Every saved draft and exported session file MUST embed croquis and satellite imagery as complete `data:image/...;base64,...` strings. Never save transient local disk paths (`/temp_assets/...`) in permanent JSON files.

### Rule 6: Object-Oriented Matplotlib Thread Isolation
Matplotlib global state (`plt.*`) is strictly forbidden on the application server. All figure plotting must use `Figure` and `FigureCanvasAgg` with `matplotlib.use('Agg')` to prevent cross-request thread contamination.

### Rule 7: Zero-PowerShell Directory Traversal
The in-app visual directory explorer must navigate the file system using Python's native `os.scandir` without invoking PowerShell or cmd processes, eliminating antivirus and AppLocker window freezes.

### Rule 8: Central Cloud Security Audit Verification
No official certificate may be printed or exported without a valid, verified cryptographic token confirmed in the Modal.com cloud audit ledger. Local offline generation of final security tokens is prohibited.

### Rule 9: Edge Headless Vector PDF Standards
PDF generation must execute via Microsoft Edge headless with `--no-pdf-header-footer` and `--run-all-compositor-stages-before-draw`. Section headers must retain the official `#D3DFEE` light-blue shading using `print-color-adjust: exact`.

### Rule 10: Modularity & Decoupling
The core GIS engine (`core_gis/`) must remain 100% decoupled from the web server (`server/`). It must never import HTTP handlers, request objects, or UI templates.

