"""
Unit Tests - CAD Croquis Generation Engine
==========================================
"""

import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3")))

from core_gis.croquis import generate_croquis_image
from core_gis.geo import validate_and_enrich_parcel


class TestCroquisEngine(unittest.TestCase):
    def test_croquis_generation(self):
        p1 = {"point_index": 1, "lon": 31.38000, "lat": 31.05000}
        p2 = {"point_index": 2, "lon": 31.38025, "lat": 31.05000}
        p3 = {"point_index": 3, "lon": 31.38025, "lat": 31.05020}
        p4 = {"point_index": 4, "lon": 31.38000, "lat": 31.05020}

        parcel = {
            "parcel_id": "test_croq",
            "applicant_name": "أحمد محمود",
            "vertices": [p1, p2, p3, p4],
            "stated_area_m2": 500.0,
            "boundaries": {
                "north": "شارع رئيسي 12م",
                "south": "أرض ملك ورثة فلان",
                "east": "جار ملاصق",
                "west": "طريق ترابي"
            }
        }
        enriched = validate_and_enrich_parcel(parcel)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            out = generate_croquis_image(enriched, tmp_path, font_size_pts=14, font_size_dims=14, font_size_text=14)
            self.assertTrue(os.path.exists(out))
            self.assertGreater(os.path.getsize(out), 5000)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
