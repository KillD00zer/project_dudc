"""
Cadastral Data Models & Schema Definitions
==========================================
Clean, typed data structures for cadastral survey parcels, vertices, and segments.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any


@dataclass
class Vertex:
    point_index: int
    lon: float
    lat: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_index": self.point_index,
            "lon": self.lon,
            "lat": self.lat
        }


@dataclass
class Segment:
    from_point: int
    to_point: int
    direction: str
    direction_name: str
    length_m: float
    azimuth_deg: float
    neighbor: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_point": self.from_point,
            "to_point": self.to_point,
            "direction": self.direction,
            "direction_name": self.direction_name,
            "length_m": self.length_m,
            "azimuth_deg": self.azimuth_deg,
            "neighbor": self.neighbor
        }


@dataclass
class Boundaries:
    north: str = ""
    south: str = ""
    east: str = ""
    west: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "north": self.north,
            "south": self.south,
            "east": self.east,
            "west": self.west
        }


@dataclass
class CadastralParcel:
    parcel_id: str
    applicant_name: str
    national_id: str = ""
    receipt_no: str = ""
    district: str = ""
    district_id: Optional[int] = None
    district_matched: bool = False
    village: str = ""
    address: str = ""
    stated_area_m2: float = 0.0
    calculated_area_m2: float = 0.0
    area_difference_m2: float = 0.0
    perimeter_m: float = 0.0
    transaction_type: str = "إنشاء"
    site_status: str = "أرض فضاء"
    request_no: str = ""
    system_officer: str = ""
    survey_technician: str = ""
    is_area_valid: bool = False
    validation_status: str = "MANUAL_REVISION"
    security_token: Optional[str] = None
    font_size_pts: int = 16
    font_size_dims: int = 16
    font_size_text: int = 16
    vertices: List[Dict[str, Any]] = field(default_factory=list)
    segments: List[Dict[str, Any]] = field(default_factory=list)
    boundaries: Dict[str, str] = field(default_factory=lambda: {"north": "", "south": "", "east": "", "west": ""})
    croquis_base64: Optional[str] = None
    satellite_base64: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
