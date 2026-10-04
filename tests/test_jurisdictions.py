"""
Unit Tests - Jurisdictions & Center Name Resolution
===================================================
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3")))

import core_gis
from core_gis.jurisdictions import resolve_center, get_center_name, list_all_centers, normalize_arabic


class TestJurisdictions(unittest.TestCase):
    def test_total_centers_count(self):
        centers = list_all_centers()
        self.assertEqual(len(centers), 18)

    def test_exact_matches(self):
        is_m, cid, name = resolve_center("المنصورة")
        self.assertTrue(is_m)
        self.assertEqual(cid, 0)
        self.assertEqual(name, "المنصورة")

        is_m, cid, name = resolve_center("طلخا")
        self.assertTrue(is_m)
        self.assertEqual(cid, 1)
        self.assertEqual(name, "طلخا")

    def test_prefixed_matches(self):
        is_m, cid, name = resolve_center("مركز المنصورة")
        self.assertTrue(is_m)
        self.assertEqual(cid, 0)

        is_m, cid, name = resolve_center("مدينة طلخا")
        self.assertTrue(is_m)
        self.assertEqual(cid, 1)

        is_m, cid, name = resolve_center("حي غرب المنصورة")
        self.assertTrue(is_m)
        self.assertEqual(cid, 0)

        is_m, cid, name = resolve_center("بندر نبروة")
        self.assertTrue(is_m)
        self.assertEqual(cid, 10)
        self.assertEqual(name, "نبروه")

    def test_unmatched_center(self):
        is_m, cid, name = resolve_center("القاهرة")
        self.assertFalse(is_m)
        self.assertEqual(cid, -1)


if __name__ == "__main__":
    unittest.main()
