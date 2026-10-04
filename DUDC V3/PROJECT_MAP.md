# خريطة النظام المعمارية وهيكل الكود المرجعي (الهندسة المعيارية)
# DUDC V3.5 Portal - Architecture & Code Map (Modular Edition)

> **الغرض من هذا الملف:** توفير دليل هندسي شامل ومركّز يوضح مسار البيانات، الترابط بين الواجهة والباك إند، ووظائف كل ملف بدقة بعد تطبيق المعيارية (Modularity) لتسهيل الصيانة وإعادة الاستخدام.

---

## 1. نظرة عامة وهيكل المجلدات المعياري (Modular Architecture)

المشروع مفكك إلى وحدات مستقلة داخل مجلد `DUDC V3`:

```text
d:\Work\GIS_tools\project_dudc\DUDC V3\
│
├── Run_DUDC_V3.bat                  # مشغل النظام الفوري (ينهي العمليات العالقة ويفتح المتصفح والسيرفر)
├── app_server.py                    # خادم التطبيق الخفيف والموجه (~130 سطر)
├── index.html                       # الواجهة الخفيفة المنظمة (~1000 سطر بدلاً من 6300+)
├── app_config.json                  # إعدادات المسارات الدائمة
├── ف.xls                            # عينة اختبارية قياسية لبيانات الرفع المساحي
│
├── [Core GIS Engine - حزمة النواة الهندسية المستقلة تماماً]:
│   └── core_gis/
│       ├── __init__.py              # تصدير الدوال والموديلات للاستخدام في أي مشروع أو سكربت
│       ├── models.py                # نماذج البيانات الصريحة (CadastralParcel, Vertex, Segment)
│       ├── geo.py                   # معالجة ملفات الرفع المساحي وحساب المساحة والتفاوت (±2.00 م²)
│       ├── croquis.py               # رسم كروكي الموقع CAD كائني التوجه (Thread-Safe Matplotlib OO)
│       ├── satellite.py             # جلب بلاطات الأقمار الصناعية وتراكب حدود المضلع
│       ├── security.py              # محرك التأمين السحابي المركزي (Modal)
│       └── jurisdictions/           # قاعدة المراكز والنطاقات الجغرافية متعددة المحافظات
│           ├── base.py              # واجهة مجردة موحدة (BaseJurisdictionProvider)
│           ├── dakahlia.py          # مراكز الدقهلية الـ 18 والمعالجة اللغوية للأسماء
│           └── resolver.py          # مسجل وموزع النطاقات الجغرافية
│
├── [Backend Services - خدمات الخادم الخلفي]:
│   └── server/
│       ├── __init__.py
│       ├── config.py                # إدارة إعدادات المسارات ومستعرض مجلدات ويندوز
│       ├── session_manager.py       # مدير الجلسات وحالة القطع المتزامنة الآمنة (Thread-Safe)
│       ├── handlers.py              # موجهات مسارات الـ REST API (GET & POST)
│       ├── pdf_service.py           # تصدير ملفات الـ PDF عبر Edge Headless
│       ├── drafts_service.py        # إدارة وحفظ واسترجاع مسودات الشهادات (JSON)
│       └── git_service.py           # خدمة فحص وسحب التحديثات من GitHub
│
├── [Modular Frontend - الواجهة الأمامية المقسمة]:
│   ├── css/
│   │   ├── main.css                 # مجمع الأنماط الرئيسي
│   │   ├── tokens.css               # المتغيرات والألوان وسمات الـ Glassmorphism
│   │   ├── layout.css               # تخطيط الصفحة وشريط المراحل الثلاث
│   │   ├── components.css           # الكروت والأزرار والمودالات والشريط العائم
│   │   ├── certificate.css          # تنسيقات ورقة الشهادة الرسمية A4
│   │   └── print.css                # قواعد الطباعة الصارمة (@media print)
│   │
│   └── js/
│       ├── state.js                 # إدارة الحالة المشتركة والتنقل بين المراحل
│       ├── drafts.js                # إدارة المسودات والحفظ التلقائي
│       ├── folder_explorer.js       # مستعرض المجلدات المرئي وفحص الصلاحيات اللحظي
│       ├── stage1.js                # استيراد ملف الرفع وفحص التفاوت واختيار المركز
│       ├── stage2.js                # استوديو التحرير الحي وضبط المسافات والعلامة المائية
│       ├── stage3.js                # الاعتماد السحابي وتصدير الحزمة والطباعة
│       └── app.js                   # ربط الأحداث وبدء التشغيل
│
├── [Backward Compatibility Facades - واجهات التوافق القديمة]:
│   ├── geo_engine.py                # يحيل مباشرة إلى core_gis.geo
│   ├── croquis_engine.py            # يحيل مباشرة إلى core_gis.croquis
│   ├── satellite_engine.py          # يحيل مباشرة إلى core_gis.satellite
│   ├── encoder_api.py               # يحيل مباشرة إلى core_gis.security
│   └── centers.py                   # يحيل مباشرة إلى core_gis.jurisdictions
│
└── [Assets & Runtime Caches]:
    ├── assets/                      # أيقونة المنظومة الرسمية والشعارات (app_icon, logos)
    ├── temp_assets/                 # كاش وقت التشغيل للكروكيات والصور الفضائية
    ├── drafts/                      # صندوق مسودات الشهادات المؤقتة (JSON)
    └── generated_certificates/      # المجلد الافتراضي لتخزين مخرجات الشهادات
```

---

## 2. جدول اتخاذ القرار السريع (Developer Decision Matrix)

| إذا كنت تريد تعديل: | الملف المطلوب مباشرة | التفاصيل ومكان العمل |
|---|---|---|
| **مستعرض مجلد الحفظ أو مسارات ويندوز** | `DUDC V3/server/config.py` + `js/folder_explorer.js` | دوال `list_subdirectories` و `openFolderExplorerModal` |
| **تعديل نصوص الشهادة أو التنسيق المرئي الحي** | `DUDC V3/js/stage2.js` | دوال `syncStage1ToStage2` و `updateSpacing` |
| **تنسيق ورقة الشهادة A4 أو الجداول** | `DUDC V3/css/certificate.css` | قواعد تنسيق الجدول والترويسة والأبعاد |
| **صندوق المسودات والحفظ المؤقت للشهادات** | `DUDC V3/server/drafts_service.py` + `js/drafts.js` | دوال `save_draft` و `load_draft` و `scheduleDraftAutoSave` |
| **تغيير ألوان أو خطوط أو أرقام كروكي الموقع CAD** | `DUDC V3/core_gis/croquis.py` | تعديل الدالة `generate_croquis_image` (Thread-Safe Matplotlib OO) |
| **تعديل منطق قراءة أعمدة ملف Excel أو حساب التفاوت** | `DUDC V3/core_gis/geo.py` | تعديل `read_survey_file` و `validate_and_enrich_parcel` |
| **تعديل تسمية ملفات ومجلدات التصدير النهائي** | `DUDC V3/server/handlers.py` | مراجعة المسار `/api/export-package` (نمط: `[العميل]-[المركز]`) |
| **تعديل طباعة وتصدير ملف الـ PDF** | `DUDC V3/server/pdf_service.py` | دالة `export_certificate_pdf` وقواعد `css/print.css` |
| **إضافة أو تعديل مراكز محافظة جديدة** | `DUDC V3/core_gis/jurisdictions/` | مصفوفات المراكز ومزود النطاقات `BaseJurisdictionProvider` |

---

## 3. قواعد ومحددات صارمة للنظام (Core Rules & Invariants)

1. **التعامل مع البيانات الناقصة:** في حال خلو خانة الرقم القومي، رقم الإيصال، أو رقم الطلب؛ يُمنع منعاً باتاً وضع بيانات وهمية أو تجريبية، ويجب أن تظهر عبارة **"لا يوجد بيانات متاحة"**.
2. **تسمية المخرجات:** مجلد العميل وكافة ملفات التصدير تُسمى حصراً بالنمط: `[اسم العميل]-[المركز]` (مثال: `أحمد محمد إبراهيم-طلخا.pdf` / `_session.json`).
3. **أزرار الواجهة:** أزرار رفع الصور المخصصة تظهر **فقط في المرحلة الأولى**، وتختفي تماماً في المرحلة الثانية والاستوديو لضمان نظافة المستند عند الطباعة.
4. **ملف الجلسة JSON:** يدمج بيانات الصورتين (الكروكي والقمر الصناعي) بتنسيق Base64 مباشرة داخل الملف لتمكين استعادة التعديلات في أي وقت دون فقدان الصور.
