"""
Unit Tests - Word (.docx) Certificate Extraction & CSV Synthesis
================================================================
"""

import os
import sys
import csv
import zipfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DUDC V3", "core_gis")))

from docx_parser import (
    clean_num_val,
    clean_text_val,
    parse_docx_certificate,
    docx_to_survey_csv
)


def create_sample_docx(file_path: str):
    """
    Creates a minimal, valid WordprocessingML .docx file containing
    a certificate metadata table and a coordinates table.
    """
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <!-- Table 0: Metadata -->
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>اسم مقدم الطلب</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>السيد أحمد علي إبراهيم</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>رقم ايصال السداد</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>789456</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الرقم القومي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>29501011234567</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>المركز</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>طلخا</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>المساحة</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>450.50 م2</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>وصف التعامل</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>إنشاء مبنى سكني</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>

    <!-- Table 1: Coordinates and Boundaries -->
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد البحري</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>شارع بعرض 12 متر</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>بطول</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>22.50</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.38150000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05120000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد القبلي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>ملك ورثة محمد حسن</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>بطول</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>22.50</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.38175000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05120000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد الشرقي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>شارع جانبي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>بطول</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>20.00</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.38175000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05100000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد الغربي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>ملك علي محمود</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>بطول</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>20.00</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.38150000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05100000</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", rels_xml)
        z.writestr("word/document.xml", document_xml)


class TestDocxParser(unittest.TestCase):
    def setUp(self):
        self.test_docx_path = os.path.join(os.path.dirname(__file__), "test_sample_cert.docx")
        self.test_csv_path = os.path.join(os.path.dirname(__file__), "test_sample_cert.csv")
        create_sample_docx(self.test_docx_path)

    def tearDown(self):
        for p in (self.test_docx_path, self.test_csv_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

    def test_clean_num_val(self):
        self.assertEqual(clean_num_val("١٢٣.٤٥"), "123.45")
        self.assertEqual(clean_num_val(" 789456 "), "789456")

    def test_parse_docx_certificate(self):
        data = parse_docx_certificate(self.test_docx_path)
        meta = data["metadata"]
        vertices = data["vertices"]
        bounds = data["boundaries"]

        self.assertEqual(meta["applicant_name"], "السيد أحمد علي إبراهيم")
        self.assertEqual(meta["receipt_no"], "789456")
        self.assertEqual(meta["national_id"], "29501011234567")
        self.assertEqual(meta["district"], "طلخا")
        self.assertAlmostEqual(meta["stated_area_m2"], 450.50)

        self.assertEqual(len(vertices), 4)
        self.assertAlmostEqual(vertices[0]["lon"], 31.38150000)
        self.assertAlmostEqual(vertices[0]["lat"], 31.05120000)

        self.assertIn("شارع بعرض 12", bounds["north"])
        self.assertIn("ورثة محمد حسن", bounds["south"])

    def test_docx_to_survey_csv(self):
        csv_path, data = docx_to_survey_csv(self.test_docx_path, self.test_csv_path)
        self.assertTrue(os.path.exists(csv_path))
        self.assertGreater(os.path.getsize(csv_path), 0)

        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 4)
            row0 = reader[0]
            self.assertEqual(row0["اسم مقدم الطلب"], "السيد أحمد علي إبراهيم")
            self.assertEqual(row0["الرقم القومي"], "29501011234567")
            self.assertEqual(row0["رقم ايصال السداد"], "789456")
            self.assertEqual(row0["المركز"], "طلخا")
            self.assertAlmostEqual(float(row0["POINT_X"]), 31.38150000)
            self.assertAlmostEqual(float(row0["POINT_Y"]), 31.05120000)

    def test_separate_tables_and_headers(self):
        """Test parsing when docx has distinct tables for metadata, boundaries, and coordinates with explicit headers."""
        doc_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <!-- Table 0: Metadata with colon syntax -->
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>اسم العميل: محمود مصطفى كامل</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>المركز: المنصورة</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>رقم ايصال السداد: ٩٩٨٨٧٧</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>المساحة: ٦٥٠.٢٥ متر مربع</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>

    <!-- Table 1: Boundaries Only -->
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>الجار</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>الطول</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد البحري</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>طريق عمومي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>25.00</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد القبلي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>ملك زيدان</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>25.00</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد الشرقي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>مسقى خاص</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>26.00</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>الحد الغربي</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>أرض زراعية</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>26.00</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>

    <!-- Table 2: Coordinates with explicit Easting/Northing headers -->
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>م</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>شرقيات (X)</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>شماليات (Y)</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>1</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.39000000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.06000000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>2</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.39050000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.06000000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>3</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.39050000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05950000</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>4</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.39000000</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>31.05950000</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
        sep_docx_path = os.path.join(os.path.dirname(__file__), "test_sep_tables.docx")
        with zipfile.ZipFile(sep_docx_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>""")
            z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>""")
            z.writestr("word/document.xml", doc_xml)

        try:
            data = parse_docx_certificate(sep_docx_path)
            meta = data["metadata"]
            bounds = data["boundaries"]
            vertices = data["vertices"]

            self.assertEqual(meta["applicant_name"], "محمود مصطفى كامل")
            self.assertEqual(meta["district"], "المنصورة")
            self.assertEqual(meta["receipt_no"], "998877")
            self.assertAlmostEqual(meta["stated_area_m2"], 650.25)

            self.assertEqual(bounds["north"], "طريق عمومي")
            self.assertEqual(bounds["south"], "ملك زيدان")
            self.assertEqual(bounds["east"], "مسقى خاص")
            self.assertEqual(bounds["west"], "أرض زراعية")

            self.assertEqual(len(vertices), 4)
            self.assertAlmostEqual(vertices[0]["lon"], 31.39000000)
            self.assertAlmostEqual(vertices[0]["lat"], 31.06000000)
        finally:
            if os.path.exists(sep_docx_path):
                os.remove(sep_docx_path)


if __name__ == "__main__":
    unittest.main()
