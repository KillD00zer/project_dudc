---
title: CSS Design System & Print Rules (css)
tags: [frontend, css, styling, glassmorphism, print-media]
related_files:
  - DUDC V3/css/main.css
  - DUDC V3/css/tokens.css
  - DUDC V3/css/layout.css
  - DUDC V3/css/components.css
  - DUDC V3/css/certificate.css
  - DUDC V3/css/print.css
---

# 💻 CSS Design System & Print Rules (`css`)

Directory: [`DUDC V3/css/`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/css/)

The styling architecture is broken into 6 modular sheets compiled via `main.css`.

---

## 🎨 Stylesheet Breakdown

| File | Purpose | Key Classes / Selectors |
|---|---|---|
| `tokens.css` | Color palette, CSS variables, typography, shadows, border radii | `:root`, `--primary-500`, `--glass-bg`, `--cert-header-blue` |
| `layout.css` | Header bar, 3-stage wizard step tabs, main content wrapper, grid layout | `.header-app`, `.stage-nav-tabs`, `.stage-view` |
| `components.css` | Modern glassmorphism cards, buttons, badges, status pills, floating toolbar, modals | `.btn-primary`, `.glass-card`, `.badge-pass`, `.modal-backdrop` |
| `certificate.css` | Exact A4 dimensions ($210\text{ mm} \times 297\text{ mm}$), table grids, borders, official seals | `#certificateSheet`, `.cert-header-table`, `.cert-grid-table` |
| `print.css` | Strict `@media print` rules, margin suppression, background color forcing | `@media print`, `@page`, `-webkit-print-color-adjust: exact` |
| `main.css` | Aggregator that imports all modular sheets | `@import "tokens.css"; ...` |

---

## 🏛️ Official Color Palette Standards
- **Section Headers & Tables Shading:** `#D3DFEE` (Official DUDC Light Blue).
- **Primary Brand Teal:** `#0E7490` / `#0891B2` (Dark cyan).
- **Legal Tolerance Pass:** `#10B981` (Emerald green).
- **Tolerance Warning / Manual Revision:** `#F59E0B` (Amber gold).
- **CAD Length Annotations:** `#D32F2F` (Bold red).
- **CAD Neighbor Annotations:** `#0284C7` (Sky blue).

---

## 🖨️ A4 Printing Constraints
- Certificate container `#certificateSheet` is fixed to $210\text{ mm} \times 297\text{ mm}$ at $96\text{ DPI}$ ($794\text{ px} \times 1123\text{ px}$).
- In `@media print`, all non-certificate UI elements (`.header-app`, `.stage-nav-tabs`, `.floating-toolbar`, `.btn-action`) are forced to `display: none !important`.

