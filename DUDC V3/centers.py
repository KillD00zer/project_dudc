"""
Official Centers Database & Morphological Processing (Facade)
=============================================================
Backward-compatible wrapper importing from the modular core_gis.jurisdictions package.
"""

from core_gis.jurisdictions import (
    resolve_center,
    get_center_name,
    get_center_id,
    list_all_centers,
    normalize_arabic,
    DAKAHLIA_CENTERS,
)

__all__ = [
    "resolve_center",
    "get_center_name",
    "get_center_id",
    "list_all_centers",
    "normalize_arabic",
    "DAKAHLIA_CENTERS",
]
