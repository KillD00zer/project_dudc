---
title: Stage 2 - Studio Editor (stage2.js)
tags: [frontend, stage2, studio, certificate, editor, typography]
related_files:
  - DUDC V3/js/stage2.js
  - DUDC V3/css/certificate.css
---

# 💻 Stage 2 - Studio Editor (`stage2.js`)

File: [`DUDC V3/js/stage2.js`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/js/stage2.js)

The interactive certificate layout studio. Provides real-time document styling, typography controls, layout spacing sliders, watermark generation, and inline editing.

---

## 🎨 Visual Spacing Engine (`updateSpacing`)

To fit varying amounts of coordinate nodes ($3 \dots 20+$ vertices) neatly onto a single A4 page without overflowing:
- A dynamic spacing slider (`#spacingSlider`) controls table cell padding, font scale, row heights, and image dimensions simultaneously.
- Applies CSS variables directly to the `#certificateSheet` container:
  ```javascript
  sheet.style.setProperty('--cert-cell-pad', `${padY}px ${padX}px`);
  sheet.style.setProperty('--cert-font-scale', `${fontScale}`);
  ```

---

## 🌊 Official Watermark Engine (`renderWatermark`)
Paints the official Dakahlia Utility Data Center crest and watermark pattern onto a background canvas:
- Dynamically resizes to match `#certificateSheet` client dimensions.
- Renders concentric rings, security rosettes, and translucent Arabic typography (`مركز معلومات شبكات المرافق - محافظة الدقهلية`).
- Opacity is dialed to a subtle, non-intrusive value ($0.08$) to ensure legibility when printed.

---

## 🔠 Studio Typography & Text Customization
Surveyors can customize fonts for individual certificate fields (e.g. applicant name, title headers, neighbor descriptions):
- **Floating Toolbar:** Highlights selected text and opens quick formatting (Bold, Italic, Color, Font Size).
- **Persistence (`collectAllTextCustomizations`):** Serializes all inline styles, font sizes, and color overrides into a clean dictionary.
- Can be saved as permanent user defaults (`/api/save-defaults`) so future certificates automatically inherit preferred styles.

---

## 🔄 Bidirectional Synchronization
- `syncStage1ToStage2(force)`: Copies coordinates, boundaries, areas, and citizen details into the certificate DOM elements.
- `syncStage2ToStage1()`: If the surveyor edits an applicant name or boundary description inside the certificate table, this function updates the underlying `activeParcel` model and Stage 1 inputs.

