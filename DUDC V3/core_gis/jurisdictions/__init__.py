"""
Regional Jurisdictions Package
==============================
"""

from .base import BaseJurisdictionProvider
from .dakahlia import DakahliaJurisdictionProvider, normalize_arabic, DAKAHLIA_CENTERS
from .resolver import (
    get_active_provider,
    set_active_provider,
    resolve_center,
    get_center_name,
    get_center_id,
    list_all_centers,
)

__all__ = [
    "BaseJurisdictionProvider",
    "DakahliaJurisdictionProvider",
    "normalize_arabic",
    "DAKAHLIA_CENTERS",
    "get_active_provider",
    "set_active_provider",
    "resolve_center",
    "get_center_name",
    "get_center_id",
    "list_all_centers",
]
