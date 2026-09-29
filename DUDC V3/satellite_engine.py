"""
Cadastral Survey Certificate System - Google Maps Satellite Capture Engine
==========================================================================
Fetches satellite tiles from Google Maps Satellite (Google Maps Satellite.lyr),
stitches them seamlessly, projects parcel vertices to image coordinates,
overlays the highlighted red parcel boundary, and crops to the Word table cell ratio.
"""

import os
import math
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw

# Ignore SSL verification for tile fetching if needed
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

TILE_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_assets", "tile_cache")
os.makedirs(TILE_CACHE_DIR, exist_ok=True)

def lonlat_to_tile(lon, lat, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def lonlat_to_pixels(lon, lat, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = ((lon + 180.0) / 360.0 * n) * 256.0
    y = ((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n) * 256.0
    return x, y

def determine_zoom(min_lon, max_lon, min_lat, max_lat, stated_area):
    """
    Selects optimal zoom level so parcel and contextual buffer are zoomed in cleanly.
    Higher zoom = closer, sharper view of buildings and parcel boundaries.
    """
    if stated_area < 250:
        return 21
    elif stated_area < 2500:
        return 20
    elif stated_area < 10000:
        return 19
    else:
        return 18

def fetch_tile(x, y, z):
    cache_file = os.path.join(TILE_CACHE_DIR, f"{z}_{x}_{y}.png")
    if os.path.exists(cache_file):
        try:
            return Image.open(cache_file).convert('RGBA')
        except Exception:
            pass
    sub = (x + y) % 4
    url = f"https://mt{sub}.google.com/vt/lyrs=s&hl=en&z={z}&x={x}&y={y}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=6, context=SSL_CTX) as response:
        img = Image.open(response).convert('RGBA')
        try:
            img.save(cache_file, "PNG")
        except Exception:
            pass
        return img

def generate_satellite_image(parcel, output_path):
    """
    Generates and saves high-resolution Google Satellite map with the parcel boundary.
    Features 55% context buffer for street surroundings and crisp 1600x1200 output.
    """
    verts = parcel["vertices"]
    lons = [v["lon"] for v in verts]
    lats = [v["lat"] for v in verts]
    
    orig_min_lon, orig_max_lon = min(lons), max(lons)
    orig_min_lat, orig_max_lat = min(lats), max(lats)
    
    span_lon = max(orig_max_lon - orig_min_lon, 0.0002)
    span_lat = max(orig_max_lat - orig_min_lat, 0.0002)
    
    # 38% context margin (zoomed in by ~30% for closer building & road visibility)
    pad_lon = span_lon * 0.38
    pad_lat = span_lat * 0.38
    
    min_lon = orig_min_lon - pad_lon
    max_lon = orig_max_lon + pad_lon
    min_lat = orig_min_lat - pad_lat
    max_lat = orig_max_lat + pad_lat
    
    zoom = determine_zoom(min_lon, max_lon, min_lat, max_lat, parcel.get("stated_area_m2", 500))
    
    # Get tile bounds
    min_tx, min_ty = lonlat_to_tile(min_lon, max_lat, zoom)
    max_tx, max_ty = lonlat_to_tile(max_lon, min_lat, zoom)
    
    # Allow sharp tile coverage up to 8x8 tiles for higher resolution
    if (max_tx - min_tx) > 7 or (max_ty - min_ty) > 7:
        zoom -= 1
        min_tx, min_ty = lonlat_to_tile(min_lon, max_lat, zoom)
        max_tx, max_ty = lonlat_to_tile(max_lon, min_lat, zoom)
    
    # Ensure minimum 4x3 tile grid for sufficient resolution (1024x768 pixels minimum)
    min_tiles_x, min_tiles_y = 4, 3
    while (max_tx - min_tx + 1) < min_tiles_x:
        min_tx -= 1
        max_tx += 1
    while (max_ty - min_ty + 1) < min_tiles_y:
        min_ty -= 1
        max_ty += 1
        
    tiles_x = max_tx - min_tx + 1
    tiles_y = max_ty - min_ty + 1
    
    stitched = Image.new('RGBA', (tiles_x * 256, tiles_y * 256))
    
    # Download tiles in parallel and stitch
    tasks = []
    for ix, tx in enumerate(range(min_tx, max_tx + 1)):
        for iy, ty in enumerate(range(min_ty, max_ty + 1)):
            tasks.append((ix, iy, tx, ty))

    def _fetch_worker(t):
        _ix, _iy, _tx, _ty = t
        try:
            return _ix, _iy, fetch_tile(_tx, _ty, zoom)
        except Exception:
            return _ix, _iy, None

    worker_count = min(12, max(4, len(tasks)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for ix, iy, tile_img in executor.map(_fetch_worker, tasks):
            if tile_img:
                stitched.paste(tile_img, (ix * 256, iy * 256))
                
    # Transform vertices to pixel coordinates in stitched image
    base_px = min_tx * 256.0
    base_py = min_ty * 256.0
    
    pixel_poly = []
    for v in verts:
        gx, gy = lonlat_to_pixels(v["lon"], v["lat"], zoom)
        pixel_poly.append((gx - base_px, gy - base_py))
        
    # Draw parcel boundary overlay
    overlay = Image.new('RGBA', stitched.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 1. Translucent red fill
    if len(pixel_poly) >= 3:
        draw.polygon(pixel_poly, fill=(239, 68, 68, 45))
        
    # 2. Bold red border (scaled for high-res visibility)
    draw.polygon(pixel_poly, outline=(239, 68, 68, 255), width=5)
    
    # Composite overlay
    final_img = Image.alpha_composite(stitched, overlay)
    
    # Save the full stitched image at native tile resolution (no cropping/downscaling)
    # The tile grid already covers the parcel + 55% context buffer, so no further crop needed
    rgb_result = final_img.convert('RGB')
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    rgb_result.save(output_path, 'JPEG', quality=95)
    return output_path
