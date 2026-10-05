"""
Cadastral Survey Certificate System - CAD Dimensions Croquis Engine
===================================================================
Renders official engineering sketch (كروكى الموقع):
- High-contrast white background.
- Thick black polygon outline.
- Numbered green vertex nodes (1, 2, ..., N) with reduced, refined font.
- Segment lengths in bold red aligned with edge angles printed INSIDE the shape.
- Neighbor descriptions in bold blue aligned with edge angles printed OUTSIDE the shape (if provided).
- Directional Compass Rose / North Arrow widget.
- Ultra High Resolution output (300 DPI / 1600x1200).
- Pure Object-Oriented Matplotlib rendering (Thread-Safe for concurrent requests).
"""

import os
import math
import numpy as np
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Polygon as MplPolygon
import matplotlib.ft2font as _mpl_ft

# Detect whether Matplotlib has native BiDi / complex text layout (Matplotlib 3.11+ via libraqm)
HAS_NATIVE_BIDI = bool(getattr(_mpl_ft, '__libraqm_version__', None))
CROQUIS_FONT_FAMILIES = ['Arial', 'Tahoma', 'Segoe UI', 'DejaVu Sans', 'sans-serif']

try:
    import arabic_reshaper
    try:
        from bidi.algorithm import get_display
    except ImportError:
        from bidi import get_display

    def shape_ar(text: Any) -> str:
        if not text:
            return ""
        s = str(text).strip()
        # In Matplotlib 3.11+ (with native libraqm BiDi support), manual reshaping/reordering
        # results in a double-reversal. Only reshape on older engines without native BiDi.
        if HAS_NATIVE_BIDI:
            return s
        reshaped = arabic_reshaper.reshape(s)
        return get_display(reshaped)
except Exception:
    def shape_ar(text: Any) -> str:
        return str(text).strip() if text else ""

AR_TO_ENG_MAP = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')


def to_eng_num(val: Any) -> str:
    if val is None:
        return ""
    return str(val).translate(AR_TO_ENG_MAP)


to_ar_num = to_eng_num


def get_edge_cardinal_direction(p1_lon: float, p1_lat: float, p2_lon: float, p2_lat: float, c_lon: float, c_lat: float) -> str:
    """
    Determines whether a segment belongs to North, South, East, or West
    relative to parcel geometry.
    """
    mid_x = (p1_lon + p2_lon) / 2.0 - c_lon
    mid_y = (p1_lat + p2_lat) / 2.0 - c_lat
    dx = p2_lon - p1_lon
    dy = p2_lat - p1_lat

    if abs(dx) > abs(dy):
        return "north" if mid_y > 0 else "south"
    else:
        return "east" if mid_x > 0 else "west"


def generate_croquis_image(
    parcel: Dict[str, Any],
    output_path: str,
    security_token: Optional[str] = None,
    font_size_pts: int = 16,
    font_size_dims: int = 16,
    font_size_text: int = 16
) -> str:
    verts = parcel["vertices"]
    segments = parcel.get("segments", [])
    bounds = parcel.get("boundaries", {})
    n_pts = len(verts)

    lons = [v["lon"] for v in verts]
    lats = [v["lat"] for v in verts]

    c_lon = float(np.mean(lons))
    c_lat = float(np.mean(lats))
    lat_scale = math.cos(math.radians(c_lat)) * 111320.0

    xs = [(lon - c_lon) * lat_scale for lon in lons]
    ys = [(lat - c_lat) * 110540.0 for lat in lats]

    pts_2d = list(zip(xs, ys))

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 10.0)
    span_y = max(max_y - min_y, 10.0)

    pad_x = span_x * 0.14
    pad_y = span_y * 0.14

    # Object-Oriented Figure (Thread-safe)
    fig = Figure(figsize=(6.5, 4.8), dpi=300)
    FigureCanvasAgg(fig)
    fig.patch.set_facecolor('white')

    ax = fig.add_subplot(111)
    ax.set_facecolor('white')

    # 1. Draw parcel polygon outline
    poly_patch = MplPolygon(pts_2d, closed=True, facecolor='none', edgecolor='black', linewidth=3.0, zorder=2)
    ax.add_patch(poly_patch)

    signed_area = 0.5 * sum(xs[i] * ys[(i + 1) % n_pts] - xs[(i + 1) % n_pts] * ys[i] for i in range(n_pts))
    is_ccw = signed_area > 0

    # 2. Vertex markers and sequential numbers
    for i in range(n_pts):
        x, y = xs[i], ys[i]
        ax.plot(x, y, marker='o', markersize=7.5, markerfacecolor='#00E676', markeredgecolor='black', markeredgewidth=1.5, zorder=4)

        dx = x - 0.0
        dy = y - 0.0
        dist_c = math.hypot(dx, dy) or 1.0
        norm_dx = dx / dist_c
        norm_dy = dy / dist_c

        v_offset = max(span_x, span_y) * 0.038
        label_x = x + norm_dx * v_offset
        label_y = y + norm_dy * v_offset

        v_idx = verts[i].get("point_index", i + 1) if isinstance(verts[i], dict) else (i + 1)
        ax.text(label_x, label_y, to_ar_num(v_idx),
                color='#3E2723', fontsize=int(font_size_pts), fontweight='bold',
                fontfamily=CROQUIS_FONT_FAMILIES, ha='center', va='center', zorder=5)

    # Map edges to cardinal directions
    side_longest_edge = {}
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        length_m = segments[i].get("length_m", 0.0) if (i < len(segments) and isinstance(segments[i], dict)) else 0.0
        side = segments[i].get("direction") if (i < len(segments) and isinstance(segments[i], dict)) else None
        if not side:
            side = get_edge_cardinal_direction(lons[i], lats[i], lons[next_i], lats[next_i], c_lon, c_lat)
        if side not in side_longest_edge or length_m > side_longest_edge[side][1]:
            side_longest_edge[side] = (i, length_m)

    # 3. Edge length (INSIDE) & neighbor (OUTSIDE)
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        x1, y1 = xs[i], ys[i]
        x2, y2 = xs[next_i], ys[next_i]

        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0

        edge_dx = x2 - x1
        edge_dy = y2 - y1
        edge_len = math.hypot(edge_dx, edge_dy) or 1.0

        angle_rad = math.atan2(edge_dy, edge_dx)
        angle_deg = math.degrees(angle_rad)

        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        if is_ccw:
            out_nx = edge_dy / edge_len
            out_ny = -edge_dx / edge_len
        else:
            out_nx = -edge_dy / edge_len
            out_ny = edge_dx / edge_len

        in_nx = -out_nx
        in_ny = -out_ny

        len_offset = min(max(span_x, span_y) * 0.042, max(edge_len * 0.22, 2.0))
        len_x = mid_x + in_nx * len_offset
        len_y = mid_y + in_ny * len_offset

        length_m = segments[i].get("length_m", edge_len) if (i < len(segments) and isinstance(segments[i], dict)) else edge_len
        len_str = shape_ar(f"م {to_ar_num(f'{length_m:.2f}')}")

        ax.text(len_x, len_y, len_str,
                color='#D32F2F', fontsize=int(font_size_dims), fontweight='bold',
                fontfamily=CROQUIS_FONT_FAMILIES, rotation=angle_deg, rotation_mode='anchor',
                ha='center', va='center', zorder=5)

        side = segments[i].get("direction") if (i < len(segments) and isinstance(segments[i], dict)) else None
        if not side:
            side = get_edge_cardinal_direction(lons[i], lats[i], lons[next_i], lats[next_i], c_lon, c_lat)

        neighbor_text = ""
        if i < len(segments) and segments[i].get("neighbor") and str(segments[i].get("neighbor")).strip():
            neighbor_text = str(segments[i].get("neighbor")).strip()
        elif side in side_longest_edge and side_longest_edge[side][0] == i:
            neighbor_text = bounds.get(side, "")

        if neighbor_text and str(neighbor_text).strip():
            neigh_offset = max(span_x, span_y) * 0.08
            neigh_x = mid_x + out_nx * neigh_offset
            neigh_y = mid_y + out_ny * neigh_offset

            ax.text(neigh_x, neigh_y, shape_ar(to_ar_num(str(neighbor_text).strip())),
                    color='#0284C7', fontsize=int(font_size_text), fontweight='bold',
                    fontfamily=CROQUIS_FONT_FAMILIES, rotation=angle_deg, rotation_mode='anchor',
                    ha='center', va='center', zorder=5)

    # 4. North Arrow at Upper-Left corner
    ax.annotate(
        '', xy=(0.06, 0.94), xytext=(0.06, 0.81), xycoords='axes fraction',
        arrowprops=dict(facecolor='black', edgecolor='black', width=2.8, headwidth=9.5, headlength=10.5, alpha=0.35),
        zorder=6
    )
    ax.text(0.06, 0.96, 'N', transform=ax.transAxes,
            color='black', fontsize=13, fontweight='bold', fontfamily=CROQUIS_FONT_FAMILIES, ha='center', va='bottom', alpha=0.45, zorder=6)

    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect('equal', adjustable='datalim')

    ax.axis('off')

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.03)

    return output_path
