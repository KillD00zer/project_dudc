"""
Unit Tests - Core Geodesic Calculations & Survey Reading
========================================================
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3")))

import core_gis
from core_gis.geo import clean_num_str, clean_id_field, clean_area_num, validate_and_enrich_parcel


class TestGeoEngine(unittest.TestCase):
    def test_clean_num_str(self):
        self.assertEqual(clean_num_str("١٢٣.٤٥"), "123.45")
        self.assertEqual(clean_num_str(" 100,50 "), "100.50")
        self.assertEqual(clean_num_str(""), "")

    def test_clean_id_field(self):
        self.assertEqual(clean_id_field("29910200000000"), "29910200000000")
        self.assertEqual(clean_id_field(29910200000000.0), "29910200000000")
        self.assertEqual(clean_id_field("0"), "")
        self.assertEqual(clean_id_field(0), "")
        self.assertEqual(clean_id_field(None), "")

    def test_area_tolerance_pass(self):
        # Coordinates around Mansoura (~31.38, 31.05)
        # Rectangle approx 20m x 20m ~ 400 m2
        p1 = {"point_index": 1, "lon": 31.38000, "lat": 31.05000}
        p2 = {"point_index": 2, "lon": 31.38021, "lat": 31.05000}
        p3 = {"point_index": 3, "lon": 31.38021, "lat": 31.05018}
        p4 = {"point_index": 4, "lon": 31.38000, "lat": 31.05018}

        parcel = {
            "parcel_id": "test_1",
            "applicant_name": "اختبار المساحة",
            "vertices": [p1, p2, p3, p4],
            "stated_area_m2": 0.0
        }
        res = validate_and_enrich_parcel(parcel)
        self.assertGreater(res["calculated_area_m2"], 350)
        self.assertLess(res["calculated_area_m2"], 450)
        self.assertEqual(len(res["segments"]), 4)

        # Stated area within ±2m2
        res["stated_area_m2"] = res["calculated_area_m2"] + 1.5
        res_pass = validate_and_enrich_parcel(res)
        self.assertTrue(res_pass["is_area_valid"])
        self.assertEqual(res_pass["validation_status"], "PASS")

        # Stated area beyond ±2m2
        res["stated_area_m2"] = res["calculated_area_m2"] + 5.0
        res_fail = validate_and_enrich_parcel(res)
        self.assertFalse(res_fail["is_area_valid"])
        self.assertEqual(res_fail["validation_status"], "MANUAL_REVISION")

    def test_read_sample_file(self):
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3", "ف.xls"))
        if os.path.exists(sample_path):
            parcels = core_gis.read_survey_file(sample_path)
            self.assertEqual(len(parcels), 1)
            p = parcels[0]
            self.assertIn("applicant_name", p)
            self.assertGreater(len(p["vertices"]), 2)
            self.assertGreater(p["calculated_area_m2"], 1000)


if __name__ == "__main__":
    unittest.main()
