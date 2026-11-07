---
title: CAD Croquis Generator (croquis.py)
tags: [core-gis, croquis, cad, matplotlib, bidi, arabic]
related_files:
  - DUDC V3/core_gis/croquis.py
  - tests/test_croquis.py
---

# 📐 CAD Croquis Generator (`croquis.py`)

File: [`DUDC V3/core_gis/croquis.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/croquis.py)

Generates official engineering survey sketches (كروكي الموقع الهندسي) with dimensional constraints, vertex callouts, neighbor annotations, and directional orientation.

---

## 🎨 Visual Specifications & Standards

| Element | Color | Font / Styling | Position / Rule |
|---|---|---|---|
| **Background** | Pure White (`#FFFFFF`) | — | High contrast for official monochrome or color printing |
| **Parcel Boundary** | Solid Black (`#000000`) | Linewidth: $2.5 \dots 4.0$ px | Closed polygon polygon |
| **Vertex Nodes** | Vivid Green (`#00E676`) | Marker: Circle with black border | Placed exactly on vertex coordinates |
| **Node Numbers** | Dark Brown (`#3E2723`) | Bold, font size: `font_size_pts` (default: 16) | Offset radially outwards from parcel centroid |
| **Edge Lengths** | Bold Red (`#D32F2F`) | Format: `م 14.25`, font size: `font_size_dims` | **INSIDE** the polygon, parallel to edge azimuth |
| **Neighbors** | Cerulean Blue (`#0284C7`) | Bold Arabic text, font size: `font_size_text` | **OUTSIDE** the polygon, parallel to edge azimuth |
| **North Arrow** | Black / Translucent | Arrow widget + 'N' label | Top-left corner ($x=0.06, y=0.94$ in axes fraction) |
| **Resolution** | — | **300 DPI** ($1600 \times 1200$) | Crisp vector rasterization |

---

## 🔤 BiDi & Complex Arabic Text Engine

A common pitfall on modern systems is Arabic characters rendering reversed or disconnected.
`croquis.py` features an adaptive text layout engine:
```python
HAS_NATIVE_BIDI = bool(getattr(_mpl_ft, '__libraqm_version__', None))

def shape_ar(text: Any) -> str:
    if not text:
        return ""
    s = str(text).strip()
    # In Matplotlib 3.11+ (with native libraqm BiDi), manual reshaping results in double-reversal
    if HAS_NATIVE_BIDI:
        return s
    reshaped = arabic_reshaper.reshape(s)
    return get_display(reshaped)
```
- It automatically detects whether Matplotlib's FreeType engine was compiled with `libraqm`.
- If native BiDi is available, it allows Matplotlib to format Arabic naturally without double-reversing.
- If running on older Matplotlib engines, it utilizes `arabic_reshaper` and `python-bidi`.
- Font fallback hierarchy: `['Arial', 'Tahoma', 'Segoe UI', 'DejaVu Sans', 'sans-serif']`.

---

## 📐 Interior vs. Exterior Normal Vector Math

To place segment lengths **inside** and neighbor descriptions **outside**, the engine calculates the polygon's signed area to determine winding order (Clockwise vs. Counter-Clockwise):
```python
signed_area = 0.5 * sum(xs[i] * ys[(i + 1) % n_pts] - xs[(i + 1) % n_pts] * ys[i] for i in range(n_pts))
is_ccw = signed_area > 0

if is_ccw:
    out_nx = edge_dy / edge_len
    out_ny = -edge_dx / edge_len
else:
    out_nx = -edge_dy / edge_len
    out_ny = edge_dx / edge_len

in_nx = -out_nx
in_ny = -out_ny
```
- Distance labels are translated along $(in\_nx, in\_ny)$.
- Neighbor descriptions are translated along $(out\_nx, out\_ny)$.
- Edge angles are clamped between $-90^\circ$ and $+90^\circ$ to prevent upside-down text.

