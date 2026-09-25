# 🏛️ Portable DUDC Cadastral Certificate Generator
### التطبيق المكتبي المحمول لإنشاء شهادات الرفع المساحي التفاعلية (DUDC)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Executable](https://img.shields.io/badge/Executable-Portable%2064--bit-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

---

## 📖 Overview / نظرة عامة
برنامج مكتبي محمول ومستقل (Portable Zero-Config Executable) يعمل على نظام ويندوز بدون الحاجة لتثبيت بايثون أو أي مكاتب خارجية، مخصص لمهندسي وفنيي المساحة بمركز معلومات شبكات المرافق بمحافظة الدقهلية (DUDC) لإنشاء شهادات إحداثيات معتمدة وفحص التفاوت القانوني للمساحة ورسم الكروكي الهندسي وجلب الصور الفضائية.

---

## 🚀 Key Features / المميزات الرئيسية
- **Zero Configuration & Portable**: Completely standalone 64-bit Windows executable (`Certificate_Generator.exe`).
- **Flexible Survey Data Ingestion**:
  - Instant drag-and-drop support for `.xls`, `.xlsx`, and `.csv` survey coordinate sheets.
  - Automatic column detection for Eastings/Northings or Longitude/Latitude.
- **Automated Geometry & Legal Validation**:
  - Dynamic parcel polygon area calculation.
  - Verifies surveyed area against registered area with official legal tolerance indicator ($\pm 2.0\text{ m}^2$).
- **CAD Croquis & Satellite Map Generation**:
  - Renders a clean CAD diagram with side dimensions, vertex tags, and a North arrow.
  - Fetches calibrated satellite imagery centered directly on the parcel polygon.
  - Allows surveyors to upload high-resolution drone/aerial imagery.
- **Word Certificate Templating & Security**:
  - Injects citizen data, parcel dimensions, neighbor descriptions, satellite photos, and CAD diagrams into the official template (`شهادة.docx`).
  - Integrated certificate security plan and digital verification (`CERTIFICATE_SECURITY_PLAN.md`).

---

## 🗂️ File Structure / هيكل الملفات
```text
├── admin_tools/                     # Security & administrative utilities (RSA keygen, validation)
├── dudc V1/                         # Version 1 application release
├── project_dudc_ V2/                # Version 2 application directory & assets
├── src/                             # Core Python source code & templates
│   ├── docx_builder.py              # Word document generator
│   ├── geo_engine.py                # Geometry calculation engine
│   ├── satellite_engine.py          # Satellite imagery fetcher
│   └── index.html                   # Modern Arabic dark-themed UI
├── CERTIFICATE_SECURITY_PLAN.md     # Official certificate anti-tamper & security architecture
├── PROJECT_DUDC_LOG.txt             # Comprehensive development & version log
└── project_dudc_V2_Portable.zip     # Portable distribution zip
```

---

## ⚡ Quick Start / طريقة التشغيل
1. افتح مجلد `project_dudc_ V2` أو `src`.
2. شغّل الملف **`run_app.bat`** (أو **`Certificate_Generator.exe`**).
3. سيفتح التطبيق تلقائياً في المتصفح على: `http://127.0.0.1:8000`.
4. ارفع ملف الإحداثيات (`.xls`, `.xlsx`, `.csv`) وراجع الكروكي واضغط إصدار الشهادة.
