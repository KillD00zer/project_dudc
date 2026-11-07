---
title: Jurisdictions & 18 Centers (jurisdictions)
tags: [core-gis, jurisdictions, dakahlia, normalization, centers]
related_files:
  - DUDC V3/core_gis/jurisdictions/base.py
  - DUDC V3/core_gis/jurisdictions/dakahlia.py
  - DUDC V3/core_gis/jurisdictions/resolver.py
  - tests/test_jurisdictions.py
---

# 📐 Jurisdictions & 18 Centers (`jurisdictions`)

Files:
- [`DUDC V3/core_gis/jurisdictions/base.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/jurisdictions/base.py)
- [`DUDC V3/core_gis/jurisdictions/dakahlia.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/jurisdictions/dakahlia.py)
- [`DUDC V3/core_gis/jurisdictions/resolver.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/jurisdictions/resolver.py)

Manages the official administrative jurisdiction registries, center matching, and morphological Arabic text normalization.

---

## 🏛️ The 18 Official Centers of Dakahlia Governorate

| ID | Arabic Name | English Name | Normalization Matches Examples |
|---|---|---|---|
| **0** | المنصورة | Mansoura | مركز المنصورة, حي شرق المنصورة, حي غرب, المنصوره |
| **1** | طلخا | Talkha | مركز طلخا, مدينة طلخا, طلخا |
| **2** | ميت غمر | Mit Ghamr | مركز ميت غمر, بندر ميت غمر |
| **3** | دكرنس | Dikirnis | مركز دكرنس, دكرنس |
| **4** | السنبلاوين | Simbillawein | مركز السنبلاوين, السنبلاوين |
| **5** | بلقاس | Bilqas | مركز بلقاس, بلقاس |
| **6** | شربين | Sherbin | مركز شربين, شربين |
| **7** | المنزلة | Manzala | مركز المنزلة, المنزله |
| **8** | منية النصر | Minyat El Nasr | مركز منية النصر, منيه النصر |
| **9** | أجا | Aga | مركز أجا, مركز اجا, أجا, اجا |
| **10** | نبروه | Nabaroh | مركز نبروه, بندر نبروة, نبروه, نبروة |
| **11** | تمي الأمديد | Temay El Amdeed | مركز تمي الأمديد, تمى الامديد |
| **12** | الجمالية | Gamaliya | مركز الجمالية, الجماليه |
| **13** | الكردي | El Kurdi | مدينة الكردي, الكردي, الكردى |
| **14** | المطرية | Matariya | مركز المطرية, المطريه |
| **15** | ميت سلسيل | Mit Salsil | مركز ميت سلسيل, ميت سلسيل |
| **16** | بني عبيد | Bani Ubaid | مركز بني عبيد, بنى عبيد |
| **17** | جمصة | Gamasa | مدينة جمصة, جمصه, جمصة |

---

## 🔤 Morphological Arabic Normalization Algorithm

Survey files typed by different agencies often have varied spelling conventions. `normalize_arabic(text)` standardizes inputs:
1. **Diacritics & Tatweel:** Removes Harakat (`[\u064B-\u065F\u0670]`) and Kashida (`ـ`).
2. **Alef Unification:** Converts `[أإآٱ]` to bare `ا`.
3. **Taa Marbuta & Haa:** Converts `ة` to `ه`.
4. **Alef Maqsura & Yaa:** Converts `ى` to `ي`.
5. **Administrative Prefixes:** Strips leading prefixes:
   - `مركز `, `مدينة `, `حي `, `قسم `, `بندر `
6. **Whitespace:** Collapses multiple spaces.

### Three-Tier Resolution Cascade
1. **Exact match:** Direct lookup in `CENTER_NAME_TO_ID`.
2. **Normalized match:** Compares normalized input to pre-computed normalized official names.
3. **Substring containment:** Matches inputs like `"حي غرب المنصورة"` $\to$ `"المنصورة"`.

---

## 🌍 Extensibility (Adding New Governorates)
The architecture supports multi-governorate deployment via `BaseJurisdictionProvider`.
To register a new governorate:
1. Subclass `BaseJurisdictionProvider` (e.g. `GharbiaJurisdictionProvider`).
2. Implement `resolve_center()`, `get_center_name()`, and `list_all_centers()`.
3. Register using `core_gis.set_active_provider(provider)`.

