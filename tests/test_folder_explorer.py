import os
import sys
import unittest
import tempfile
import shutil

# Add DUDC V3 to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUDC_V3_DIR = os.path.join(BASE_DIR, "DUDC V3")
if DUDC_V3_DIR not in sys.path:
    sys.path.insert(0, DUDC_V3_DIR)

from server.config import (
    get_quick_locations,
    get_system_drives,
    list_subdirectories,
    create_subdirectory,
    validate_path_status
)

class TestFolderExplorer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="dudc_test_explorer_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_quick_locations(self):
        locs = get_quick_locations()
        self.assertIsInstance(locs, list)
        self.assertGreaterEqual(len(locs), 2)
        paths = [item["path"] for item in locs]
        for p in paths:
            self.assertTrue(isinstance(p, str))

    def test_get_system_drives(self):
        drives = get_system_drives()
        self.assertIsInstance(drives, list)
        # On Windows there is at least C:\
        if os.name == 'nt':
            self.assertGreaterEqual(len(drives), 1)

    def test_list_and_create_subdirectories(self):
        # Create test subfolder
        sub1 = os.path.join(self.temp_dir, "Certificates_2026")
        os.makedirs(sub1, exist_ok=True)

        res = list_subdirectories(self.temp_dir)
        self.assertTrue(res["success"])
        self.assertEqual(res["current_path"], self.temp_dir)
        self.assertTrue(res["can_write"])
        names = [s["name"] for s in res["subdirectories"]]
        self.assertIn("Certificates_2026", names)

        # Test creating a new subdirectory
        new_res = create_subdirectory(self.temp_dir, "Subfolder_Test")
        self.assertTrue(new_res["success"])
        self.assertTrue(os.path.isdir(os.path.join(self.temp_dir, "Subfolder_Test")))

    def test_validate_path_status(self):
        # Existing writable path
        val1 = validate_path_status(self.temp_dir)
        self.assertTrue(val1["valid"])
        self.assertTrue(val1["exists"])
        self.assertTrue(val1["can_write"])

        # Non-existing but creatable path
        future_path = os.path.join(self.temp_dir, "new_folder_to_create")
        val2 = validate_path_status(future_path)
        self.assertTrue(val2["valid"])
        self.assertFalse(val2["exists"])
        self.assertTrue(val2["can_create"])

        # Empty path falls back to safe default directory
        val_empty = validate_path_status("")
        self.assertTrue(val_empty["valid"])
        self.assertTrue(bool(val_empty["path"]))

        # Invalid path with question mark or non-existent root drive
        val_invalid = validate_path_status("D:\\Invalid?Folder*Name")
        self.assertFalse(val_invalid["valid"])

if __name__ == "__main__":
    unittest.main()
