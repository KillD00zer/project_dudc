---
title: PDF Exporter (pdf_service.py)
tags: [backend, pdf, edge, headless, vector]
related_files:
  - DUDC V3/server/pdf_service.py
  - DUDC V3/css/print.css
---

# ⚙️ PDF Exporter (`pdf_service.py`)

File: [`DUDC V3/server/pdf_service.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/server/pdf_service.py)

Automates Microsoft Edge in headless mode to render HTML certificate markup directly into high-fidelity, vector-crisp A4 PDF documents.

---

## 🖨️ Why Headless Edge?
1. **Pre-installed on All Windows PCs:** Microsoft Edge is native to Windows 10 and 11, requiring zero third-party PDF printers or heavy binary installations like wkhtmltopdf.
2. **Precise CSS Paged Media Support:** Perfectly respects CSS `@page`, `@media print`, flexbox, and complex Arabic typography.
3. **Vector Quality:** Text, table borders, and vector watermarks remain scalable without pixelation.

---

## 🛠️ Execution Pipeline & Flags

```python
cmd = [
    edge_exe,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={output_pdf_path}",
    temp_html_path
]
```

### Critical Flags Explained
- `--headless`: Runs Chromium engine in the background without opening a browser window.
- `--no-pdf-header-footer`: Strips default browser headers (URL, page numbers, date) for clean official document layout.
- `--run-all-compositor-stages-before-draw`: Crucial for rendering high-DPI images, watermarks, and Arabic glyph layouts before capturing the PDF snapshot.

---

## 🎨 Print CSS Media Rules (`css/print.css`)
To force Edge to print background colors (such as the official `#D3DFEE` light-blue section header shading):
```css
@media print {
  body {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
  @page {
    size: A4 portrait;
    margin: 5mm;
  }
}
```

