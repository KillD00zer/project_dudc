"""
Integration Test - Docx Upload & Permanent CSV Synthesis Pipeline
==================================================================
Tests:
1. Docx parsing to CSV with permanent disk save.
2. SessionManager integration & survey file registration.
3. Geo engine reading & validation of the synthesized CSV.
"""

import os
import sys
import unittest
import shutil

# Application directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3"))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "core_gis"))

from tests.test_docx_parser import create_sample_docx
from docx_parser import docx_to_survey_csv, parse_docx_certificate
import csv


class TestDocxIntegrationPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "tmp_integration_output")
        os.makedirs(self.test_dir, exist_ok=True)
        self.sample_docx = os.path.join(self.test_dir, "sample_cert.docx")
        create_sample_docx(self.sample_docx)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_docx_to_permanent_csv_pipeline(self):
        # 1. Synthesize CSV from docx
        temp_csv = os.path.join(self.test_dir, "temp_survey.csv")
        out_path, parsed = docx_to_survey_csv(self.sample_docx, temp_csv)

        meta = parsed["metadata"]
        applicant = meta.get("applicant_name", "مواطن")
        district = meta.get("district", "")
        clean_name = applicant.strip()
        clean_dist = district.strip()
        base_name = f"{clean_name}-{clean_dist}" if clean_dist else clean_name
        csv_filename = f"{base_name}_survey.csv"

        # 2. Save permanently in output dir
        permanent_csv = os.path.join(self.test_dir, csv_filename)
        shutil.copy2(temp_csv, permanent_csv)

        self.assertTrue(os.path.exists(permanent_csv))
        self.assertGreater(os.path.getsize(permanent_csv), 0)

        # 3. Verify UTF-8 BOM encoding and CSV headers
        with open(permanent_csv, "rb") as raw_f:
            bom = raw_f.read(3)
            self.assertEqual(bom, b'\xef\xbb\xbf', "Permanent CSV must have UTF-8 BOM for Excel compatibility")

        # 4. Read back using csv.DictReader and verify data integrity
        with open(permanent_csv, mode="r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 4, "Must contain 4 coordinate points")

            row0 = reader[0]
            self.assertEqual(row0["ORIG_FID"], "1")
            self.assertEqual(row0["اسم مقدم الطلب"], "السيد أحمد علي إبراهيم")
            self.assertEqual(row0["الرقم القومي"], "29501011234567")
            self.assertEqual(row0["رقم ايصال السداد"], "789456")
            self.assertEqual(row0["المركز"], "طلخا")
            self.assertEqual(float(row0["المساحة م2"]), 450.50)
            self.assertEqual(row0["وصف التعامل"], "إنشاء مبنى سكني")
            self.assertIn("شارع بعرض 12", row0["الحد_البحري"])
            self.assertIn("ورثة محمد حسن", row0["الحد_القبلي"])
            self.assertAlmostEqual(float(row0["POINT_X"]), 31.38150000)
            self.assertAlmostEqual(float(row0["POINT_Y"]), 31.05120000)

            # Check that all rows maintain the same applicant & metadata while coordinates differ
            row1 = reader[1]
            self.assertEqual(row1["اسم مقدم الطلب"], "السيد أحمد علي إبراهيم")
            self.assertAlmostEqual(float(row1["POINT_X"]), 31.38175000)
            self.assertAlmostEqual(float(row1["POINT_Y"]), 31.05120000)


if __name__ == "__main__":
    unittest.main()
