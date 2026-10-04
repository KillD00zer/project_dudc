"""
Cadastral Survey Certificate System - CAD Dimensions Croquis Engine (Facade)
============================================================================
Backward-compatible wrapper importing from the modular core_gis.croquis package.
"""

from core_gis.croquis import (
    generate_croquis_image,
    shape_ar,
    to_ar_num,
    to_eng_num,
    get_edge_cardinal_direction,
)

__all__ = [
    "generate_croquis_image",
    "shape_ar",
    "to_ar_num",
    "to_eng_num",
    "get_edge_cardinal_direction",
]
