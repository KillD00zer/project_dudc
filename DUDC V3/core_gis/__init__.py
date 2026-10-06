"""
DUDC Core GIS & Cadastral Engine
================================
Modular, standalone cadastral engineering library.
Can be imported into any web server, QGIS plugin, ArcGIS Pro toolbox, or CLI script.
"""

from .models import CadastralParcel, Vertex, Segment, Boundaries
from .geo import read_survey_file, validate_and_enrich_parcel, clean_id_field, clean_num_str
from .croquis import generate_croquis_image
from .satellite import generate_satellite_image
from .security import generate_dudc_token, confirm_cloud_issuance, TRIAL_TOKEN
from .jurisdictions import (
    resolve_center,
    get_center_name,
    get_center_id,
    list_all_centers,
    normalize_arabic,
    DAKAHLIA_CENTERS,
)

__version__ = "4.0.0"

__all__ = [
    "CadastralParcel",
    "Vertex",
    "Segment",
    "Boundaries",
    "read_survey_file",
    "validate_and_enrich_parcel",
    "clean_id_field",
    "clean_num_str",
    "generate_croquis_image",
    "generate_satellite_image",
    "generate_dudc_token",
    "confirm_cloud_issuance",
    "TRIAL_TOKEN",
    "resolve_center",
    "get_center_name",
    "get_center_id",
    "list_all_centers",
    "normalize_arabic",
    "DAKAHLIA_CENTERS",
]
