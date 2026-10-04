"""
Cadastral Survey Certificate System - Core Geo & Validation Engine (Facade)
===========================================================================
Backward-compatible wrapper importing from the modular core_gis.geo package.
"""

from core_gis.geo import (
    read_survey_file,
    validate_and_enrich_parcel,
    clean_text_val,
    clean_num_str,
    clean_id_field,
    clean_area_num,
    GEOD,
    ARABIC_TO_ENG,
)

__all__ = [
    "read_survey_file",
    "validate_and_enrich_parcel",
    "clean_text_val",
    "clean_num_str",
    "clean_id_field",
    "clean_area_num",
    "GEOD",
    "ARABIC_TO_ENG",
]
