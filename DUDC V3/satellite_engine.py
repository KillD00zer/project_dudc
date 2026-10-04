"""
Cadastral Survey Certificate System - Satellite Imagery Capture Engine (Facade)
===============================================================================
Backward-compatible wrapper importing from the modular core_gis.satellite package.
"""

from core_gis.satellite import (
    generate_satellite_image,
    lonlat_to_tile,
    lonlat_to_pixels,
    determine_zoom,
    fetch_tile,
)

__all__ = [
    "generate_satellite_image",
    "lonlat_to_tile",
    "lonlat_to_pixels",
    "determine_zoom",
    "fetch_tile",
]
