"""
Base Jurisdiction Provider Interface
====================================
Defines the contract for regional centers, directorates, and administrative divisions.
Allows the system to be reused for Dakahlia, Gharbia, Cairo, or any other Egyptian governorate.
"""

from abc import ABC, abstractmethod
from typing import Tuple, List


class BaseJurisdictionProvider(ABC):
    @property
    @abstractmethod
    def governorate_name(self) -> str:
        """Name of the governorate (e.g. 'الدقهلية')."""
        pass

    @abstractmethod
    def resolve_center(self, raw_name: str) -> Tuple[bool, int, str]:
        """
        Resolves a raw input string into (is_matched, center_id, canonical_name).
        """
        pass

    @abstractmethod
    def get_center_name(self, center_id: int) -> str:
        """
        Returns the official Arabic name for a given center ID.
        """
        pass

    @abstractmethod
    def list_all_centers(self) -> List[Tuple[int, str]]:
        """
        Returns a list of all official centers: [(0, 'المنصورة'), (1, 'طلخا'), ...].
        """
        pass
