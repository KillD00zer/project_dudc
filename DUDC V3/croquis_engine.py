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
"""

import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, FancyArrowPatch, Circle

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def shape_ar(text):
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
except Exception:
    def shape_ar(text):
        return str(text) if text else ""

AR_DIGITS_MAP = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')

def to_ar_num(val):
    if val is None:
        return ""
    return str(val).translate(AR_DIGITS_MAP)

def get_edge_cardinal_direction(p1_lon, p1_lat, p2_lon, p2_lat, c_lon, c_lat):
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

def generate_croquis_image(parcel, output_path, security_token=None, font_size_pts=16, font_size_dims=16, font_size_text=16):
    verts = parcel["vertices"]
    segments = parcel.get("segments", [])
    bounds = parcel.get("boundaries", {})
    n_pts = len(verts)
    
    lons = [v["lon"] for v in verts]
    lats = [v["lat"] for v in verts]
    
    # Local metric Cartesian projection centered on parcel centroid
    c_lon = float(np.mean(lons))
    c_lat = float(np.mean(lats))
    lat_scale = math.cos(math.radians(c_lat)) * 111320.0
    
    xs = [(lon - c_lon) * lat_scale for lon in lons]
    ys = [(lat - c_lat) * 110540.0 for lat in lats]
    
    pts_2d = list(zip(xs, ys))
    
    # Calculate bounds & span
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 10.0)
    span_y = max(max_y - min_y, 10.0)
    
    # Compact margin for aligned text and north arrow
    pad_x = span_x * 0.14
    pad_y = span_y * 0.14
    
    fig, ax = plt.subplots(figsize=(6.5, 4.8), dpi=300)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # 1. Draw parcel polygon outline with strong line weight
    poly_patch = MplPolygon(pts_2d, closed=True, facecolor='none', edgecolor='black', linewidth=3.0, zorder=2)
    ax.add_patch(poly_patch)
    
    # Determine polygon orientation (clockwise vs counter-clockwise)
    signed_area = 0.5 * sum(xs[i] * ys[(i + 1) % n_pts] - xs[(i + 1) % n_pts] * ys[i] for i in range(n_pts))
    is_ccw = signed_area > 0
    
    # 2. Vertex markers and sequential numbers (reduced font size)
    for i in range(n_pts):
        x, y = xs[i], ys[i]
        
        # Bright green vertex circle with dark border
        ax.plot(x, y, marker='o', markersize=7.5, markerfacecolor='#00E676', markeredgecolor='black', markeredgewidth=1.5, zorder=4)
        
        # Outward direction from centroid
        dx = x - 0.0
        dy = y - 0.0
        dist_c = math.hypot(dx, dy) or 1.0
        norm_dx = dx / dist_c
        norm_dy = dy / dist_c
        
        # Position number slightly outside vertex
        v_offset = max(span_x, span_y) * 0.038
        label_x = x + norm_dx * v_offset
        label_y = y + norm_dy * v_offset
        
        # Dark brown vertex font (configurable fontsize, default 11 bold)
        ax.text(label_x, label_y, to_ar_num(verts[i]["point_index"]), 
                color='#3E2723', fontsize=int(font_size_pts), fontweight='bold',
                fontfamily='Arial', ha='center', va='center', zorder=5)
        
    # Map edges to cardinal neighbor descriptions
    side_longest_edge = {}
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        length_m = segments[i]["length_m"] if i < len(segments) else 0.0
        # Check if segment has user-selected direction
        side = segments[i].get("direction") if i < len(segments) else None
        if not side:
            side = get_edge_cardinal_direction(verts[i]["lon"], verts[i]["lat"], verts[next_i]["lon"], verts[next_i]["lat"], c_lon, c_lat)
        if side not in side_longest_edge or length_m > side_longest_edge[side][1]:
            side_longest_edge[side] = (i, length_m)

    # 3. Segment length (INSIDE shape) & neighbor annotations (OUTSIDE shape if provided)
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        x1, y1 = xs[i], ys[i]
        x2, y2 = xs[next_i], ys[next_i]
        
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        
        edge_dx = x2 - x1
        edge_dy = y2 - y1
        edge_len = math.hypot(edge_dx, edge_dy) or 1.0
        
        # Calculate angle of edge in degrees
        angle_rad = math.atan2(edge_dy, edge_dx)
        angle_deg = math.degrees(angle_rad)
        
        # Keep text readable from bottom/right (never upside down)
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180
            
        # Outward unit normal
        if is_ccw:
            out_nx = edge_dy / edge_len
            out_ny = -edge_dx / edge_len
        else:
            out_nx = -edge_dy / edge_len
            out_ny = edge_dx / edge_len
            
        # Inward unit normal (pointing INSIDE the polygon)
        in_nx = -out_nx
        in_ny = -out_ny
        
        # Length offset: positioned INSIDE the shape
        len_offset = min(max(span_x, span_y) * 0.042, max(edge_len * 0.22, 2.0))
        len_x = mid_x + in_nx * len_offset
        len_y = mid_y + in_ny * len_offset
        
        length_m = segments[i]["length_m"] if i < len(segments) else edge_len
        len_str = f"م {to_ar_num(f'{length_m:.2f}')}"
        
        # Draw red length label aligned with segment INSIDE the polygon
        ax.text(len_x, len_y, len_str,
                color='#D32F2F', fontsize=int(font_size_dims), fontweight='bold',
                fontfamily='Arial', rotation=angle_deg, rotation_mode='anchor',
                ha='center', va='center', zorder=5)
        
        # Check if this edge has a neighbor description (only drawn if provided by user)
        side = segments[i].get("direction") if i < len(segments) else None
        if not side:
            side = get_edge_cardinal_direction(verts[i]["lon"], verts[i]["lat"], verts[next_i]["lon"], verts[next_i]["lat"], c_lon, c_lat)
            
        neighbor_text = ""
        # 1. Per-segment specific neighbor if given
        if i < len(segments) and segments[i].get("neighbor") and str(segments[i].get("neighbor")).strip():
            neighbor_text = str(segments[i].get("neighbor")).strip()
        # 2. Or cardinal boundary neighbor if edge is the longest edge for that direction
        elif side in side_longest_edge and side_longest_edge[side][0] == i:
            neighbor_text = bounds.get(side, "")
            
        if neighbor_text and str(neighbor_text).strip():
            neigh_offset = max(span_x, span_y) * 0.08
            neigh_x = mid_x + out_nx * neigh_offset
            neigh_y = mid_y + out_ny * neigh_offset
            
            # Draw blue neighbor text aligned with segment OUTSIDE the polygon
            ax.text(neigh_x, neigh_y, shape_ar(to_ar_num(str(neighbor_text).strip())),
                    color='#0284C7', fontsize=int(font_size_text), fontweight='bold',
                    fontfamily='Arial', rotation=angle_deg, rotation_mode='anchor',
                    ha='center', va='center', zorder=5)
        
    # 4. Add Semi-Transparent Compass Rose / North Arrow at Upper-Left corner
    ax.annotate(
        '', xy=(0.06, 0.94), xytext=(0.06, 0.81), xycoords='axes fraction',
        arrowprops=dict(facecolor='black', edgecolor='black', width=2.8, headwidth=9.5, headlength=10.5, alpha=0.35),
        zorder=6
    )
    ax.text(0.06, 0.96, 'N', transform=ax.transAxes,
            color='black', fontsize=13, fontweight='bold', fontfamily='Arial', ha='center', va='bottom', alpha=0.45, zorder=6)
    
    # 5. Cryptographic Security Token Watermark (Background Layer)
    if security_token:
        ax.text(
            0.5, 0.5,
            str(security_token).strip(),
            transform=ax.transAxes,
            color='#64748B', fontsize=13, fontweight='bold', fontfamily='Consolas',
            rotation=25, alpha=0.18,
            ha='center', va='center',
            zorder=1
        )
    
    # Set view limits with uniform aspect ratio
    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect('equal', adjustable='datalim')
    
    # Hide all frame borders and axes
    ax.axis('off')
    plt.tight_layout(pad=0.06)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.03)
    plt.close(fig)
    return output_path
