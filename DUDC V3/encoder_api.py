"""
DUDC Secure Token Client - Facade
=================================
Backward-compatible wrapper importing from the modular core_gis.security package.
"""

from core_gis.security import (
    generate_dudc_token,
    confirm_cloud_issuance,
    CLOUD_ENDPOINT,
    CONFIRM_ENDPOINT,
    OFFICE_API_KEY,
    TRIAL_TOKEN,
)

__all__ = [
    "generate_dudc_token",
    "confirm_cloud_issuance",
    "CLOUD_ENDPOINT",
    "CONFIRM_ENDPOINT",
    "OFFICE_API_KEY",
    "TRIAL_TOKEN",
]
