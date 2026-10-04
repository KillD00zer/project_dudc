"""
Jurisdiction Resolver Registry
==============================
Provides high-level helpers to resolve center names and list centers using the active provider.
Defaults to Dakahlia Governorate, but supports registering new governorates dynamically.
"""

from typing import Tuple, List, Optional
from .base import BaseJurisdictionProvider
from .dakahlia import DakahliaJurisdictionProvider, normalize_arabic

_ACTIVE_PROVIDER: BaseJurisdictionProvider = DakahliaJurisdictionProvider()


def get_active_provider() -> BaseJurisdictionProvider:
    global _ACTIVE_PROVIDER
    return _ACTIVE_PROVIDER


def set_active_provider(provider: BaseJurisdictionProvider):
    global _ACTIVE_PROVIDER
    _ACTIVE_PROVIDER = provider


def resolve_center(raw_name: str) -> Tuple[bool, int, str]:
    return get_active_provider().resolve_center(raw_name)


def get_center_name(center_id: int) -> str:
    return get_active_provider().get_center_name(center_id)


def get_center_id(name: str) -> int:
    is_matched, cid, _ = resolve_center(name)
    return cid if is_matched else 0


def list_all_centers() -> List[Tuple[int, str]]:
    return get_active_provider().list_all_centers()
