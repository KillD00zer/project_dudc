# خريطة المشروع وهيكل الكود المرجعي (الهندسة المعيارية)
# DUDC V4.0 Portal - Modular Architecture & Code Map (Portable Edition)

> **الغرض:** دليل هندسي شامل ومركّز يوضح مسار البيانات، الترابط بين الواجهة والباك إند، ووظائف كل ملف بدقة بعد تطبيق المعيارية (Modularity) لتسهيل الصيانة وإعادة الاستخدام.

👉 **النسخة الكاملة المفصلة متوفرة داخل مجلد النظام:**  
[DUDC V3/PROJECT_MAP.md](file:///d:/Work/GIS_tools/project_dudc/DUDC%20V3/PROJECT_MAP.md)

---

## 1. الهيكل المعماري المعياري (Modular Structure)

```text
d:\Work\GIS_tools\project_dudc\
│
├── tests/                           # الاختبارات الآلية القياسية (16 اختباراً شاملاً)
│   ├── test_geo.py                  # فحص حسابات المساحة والتفاوت (±2.00 م²)
│   ├── test_jurisdictions.py        # فحص تطبيع ومطابقة المراكز الرسمية
│   ├── test_croquis.py              # فحص توليد الكروكي الهندسي
│   ├── test_folder_explorer.py      # فحص مستعرض المجلدات والتحقق من الصلاحيات
│   └── test_endpoints.py            # فحص موجهات الـ REST API والخدمات
│
├── DUDC V3/                         # المجلد النشط والمستقل للنظام
│   ├── app_server.py                # نقطة انطلاق السيرفر الخفيفة الموجهة (~170 سطر)
│   ├── index.html                   # هيكل الواجهة الخفيف المنسق (~1000 سطر)
│   │
│   ├── core_gis/                    # حزمة النواة الهندسية المستقلة تماماً (Standalone GIS Engine)
│   │   ├── models.py                # نماذج البيانات الصريحة (CadastralParcel, Vertex, Segment)
│   │   ├── geo.py                   # قراءة ملفات Excel/CSV وحساب المساحة والتفاوت الجيوديسي
│   │   ├── croquis.py               # رسم كروكي الموقع الهندسي CAD (Thread-Safe Matplotlib OO)
│   │   ├── satellite.py             # جلب بلاطات القمر الصناعي وتراكب حدود المضلع
│   │   ├── security.py              # كود التأمين السحابي المركزي (Modal)
│   │   └── jurisdictions/           # قاعدة المراكز والنطاقات الجغرافية متعددة المحافظات
│   │
│   ├── server/                      # خدمات السيرفر الخلفي المفككة
│   │   ├── config.py                # الإعدادات ومستعرض المجلدات والتحقق من المسارات
│   │   ├── session_manager.py       # إدارة الجلسات وحالة القطع المتزامنة الآمنة (Thread-Safe)
│   │   ├── handlers.py              # موجهات مسارات الـ REST API (GET & POST)
│   │   ├── pdf_service.py           # تصدير الـ PDF عبر Edge Headless
│   │   ├── drafts_service.py        # إدارة وحفظ مسودات الشهادات (JSON + Base64)
│   │   └── git_service.py           # خدمة التحديث التلقائي عبر GitHub
│   │
│   ├── css/                         # أنماط التصميم المفصولة
│   │   ├── main.css                 # مجمع الأنماط الرئيسي
│   │   ├── tokens.css               # المتغيرات والألوان وسمات الـ Glassmorphism
│   │   ├── layout.css               # تخطيط الصفحة وشريط المراحل الثلاث
│   │   ├── components.css           # الكروت والأزرار والمودالات والشريط العائم
│   │   ├── certificate.css          # تنسيقات ورقة الشهادة الرسمية A4
│   │   └── print.css                # قواعد الطباعة الصارمة (@media print)
│   │
│   └── js/                          # منطق الواجهة المقسم لوحدات مستقلة
│       ├── state.js                 # إدارة الحالة المشتركة والتنقل بين المراحل
│       ├── drafts.js                # إدارة المسودات والحفظ التلقائي
│       ├── folder_explorer.js       # مستعرض المجلدات المرئي وفحص الصلاحيات اللحظي
│       ├── stage1.js                # استيراد ملف الرفع وفحص التفاوت واختيار المركز
│       ├── stage2.js                # استوديو التحرير الحي وضبط المسافات والعلامة المائية
│       ├── stage3.js                # الاعتماد السحابي وتصدير الحزمة والطباعة
│       └── app.js                   # ربط الأحداث وبدء التشغيل
│
├── Run_DUDC_V3.bat                  # مشغل النظام بنقرة واحدة
├── Update_DUDC_V3.bat               # اختصار التحديث من GitHub
└── README.md                        # التوثيق الشامل للنظام
```

---

## 2. جدول اتخاذ القرار السريع (Developer Decision Matrix)

| إذا كنت تريد تعديل: | الملف المطلوب مباشرة | الوظيفة / الدالة الأساسية |
|---|---|---|
| **مستعرض مجلد الحفظ أو مسارات ويندوز** | `DUDC V3/server/config.py` + `js/folder_explorer.js` | دوال `list_subdirectories` و `openFolderExplorerModal` |
| **بيانات أو نصوص أو واجهة الاستوديو** | `DUDC V3/js/stage2.js` | دوال `syncStage1ToStage2` و `updateSpacing` |
| **تنسيق ورقة الشهادة A4** | `DUDC V3/css/certificate.css` | قواعد تنسيق الجدول والترويسة والأبعاد |
| **صندوق المسودات والحفظ المؤقت** | `DUDC V3/server/drafts_service.py` + `js/drafts.js` | دوال `save_draft` و `load_draft` و `scheduleDraftAutoSave` |
| **تصدير الـ PDF عبر Edge أو تسمية الملفات** | `DUDC V3/server/pdf_service.py` | دالة `export_certificate_pdf` |
| **رسم أضلاع وأبعاد كروكي الموقع CAD** | `DUDC V3/core_gis/croquis.py` | دالة `generate_croquis_image` (Thread-Safe) |
| **قراءة ملف الرفع Excel أو حساب المساحة** | `DUDC V3/core_gis/geo.py` | دالة `read_survey_file` و `validate_and_enrich_parcel` |
| **كود التأمين والرقابة السحابية** | `DUDC V3/core_gis/security.py` | دالة `generate_dudc_token` |
| **مراكز الدقهلية أو إضافة محافظة جديدة** | `DUDC V3/core_gis/jurisdictions/` | مزود النطاقات `BaseJurisdictionProvider` و `dakahlia.py` |

---

## 3. محددات وثوابت العمل الصارمة
1. **تسمية مخرجات العميل:** المجلد وكافة ملفات التصدير تُسمى حصراً: `[اسم العميل]-[المركز]` (مثال: `أحمد محمد إبراهيم-طلخا.pdf` / `_session.json`).
2. **البيانات غير المتوفرة:** إذا كانت الخانة فارغة أو 0، يُعرض نص **"لا يوجد بيانات متاحة"** ويُمنع أي نص عشوائي أو افتراضي.
3. **أزرار رفع الصور:** موجودة حصراً في **المرحلة الأولى فقط**، وممنوعة تماماً من الظهور في المرحلة الثانية والاستوديو لضمان نظافة الطباعة.
