---
title: Satellite Tile Engine (satellite.py)
tags: [core-gis, satellite, tiles, multithreading, pillow]
related_files:
  - DUDC V3/core_gis/satellite.py
---

# 📐 Satellite Tile Engine (`satellite.py`)

File: [`DUDC V3/core_gis/satellite.py`](file:///d:/Work/certi_processing_tools/project_dudc/DUDC%20V3/core_gis/satellite.py)

Captures high-definition satellite imagery, stitches Web Mercator tiles, projects WGS84 parcel vertices into pixel coordinates, highlights the parcel polygon, and outputs high-quality JPEG images.

---

## 🛰️ Web Mercator Mathematics & Tile Math

The engine operates on Spherical Mercator (EPSG:3857):

1. **Coordinate to Tile Index:**
   $$\text{lat\_rad} = \text{radians}(\text{lat})$$
   $$n = 2^{\text{zoom}}$$
   $$\text{xtile} = \left\lfloor \frac{\text{lon} + 180}{360} \times n \right\rfloor$$
   $$\text{ytile} = \left\lfloor \left( 1 - \frac{\text{asinh}(\tan(\text{lat\_rad}))}{\pi} \right) \times \frac{n}{2} \right\rfloor$$

2. **Coordinate to Global Pixel Space ($256 \times 256$ per tile):**
   $$x_{px} = \frac{\text{lon} + 180}{360} \times n \times 256$$
   $$y_{px} = \left( 1 - \frac{\text{asinh}(\tan(\text{lat\_rad}))}{\pi} \right) \times \frac{n}{2} \times 256$$

---

## 🎯 Adaptive Zoom Level Determination

Zoom levels are selected dynamically based on parcel area:
- $\text{Area} < 250\text{ m}^2 \implies \mathbf{Zoom\ 21}$ (High building detail)
- $250\text{ m}^2 \le \text{Area} < 2500\text{ m}^2 \implies \mathbf{Zoom\ 20}$
- $2500\text{ m}^2 \le \text{Area} < 10000\text{ m}^2 \implies \mathbf{Zoom\ 19}$
- $\text{Area} \ge 10000\text{ m}^2 \implies \mathbf{Zoom\ 18}$

If the bounding box spans more than 7 tiles in either direction, zoom is automatically decremented by 1 to prevent excessive bandwidth usage.

---

## ⚡ Concurrency & Disk Caching
- **Multi-threaded Fetcher:** Uses Python's `ThreadPoolExecutor` (4 to 12 concurrent workers) for fast tile downloading.
- **Disk Cache:** Cached in `DUDC V3/temp_assets/tile_cache/{z}_{x}_{y}.png` to avoid re-downloading identical tiles across runs.
- **Vector Overlay:** Uses Pillow `ImageDraw.polygon`:
  - Semi-transparent fill: Red RGBA `(239, 68, 68, 45)`.
  - Solid border outline: Red RGBA `(239, 68, 68, 255)`, width: 5 px.
- **Output:** Stitched and alpha-composited into an RGB JPEG with 95% quality.

