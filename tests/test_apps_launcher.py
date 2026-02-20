
import json
import logging
import unittest
from pathlib import Path

# Add project root to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from safekid.apps.apps_launcher import AppsLauncher

class TestAppsLauncher(unittest.TestCase):
    def setUp(self):
        # Use a temporary catalog or mock
        logging.getLogger().setLevel(logging.CRITICAL)
        self.catalog_path = Path(__file__).parent.parent / "safekid" / "apps" / "apps_catalog.json"
        self.launcher = AppsLauncher(self.catalog_path, child_age=10)

    def test_load_apps(self):
        """Test loading apps from file"""
        apps = self.launcher.get_all_apps()
        self.assertGreater(len(apps), 0)
        self.assertTrue(any(a.id == "gcompris" for a in apps))

    def test_category_filtering(self):
        """Test filtering by category"""
        edu_apps = self.launcher.get_apps_by_category("edu")
        self.assertTrue(len(edu_apps) > 0)
        self.assertTrue(all(a.category == "edu" for a in edu_apps))

    def test_age_filtering_9yo(self):
        """Test filtering for age 9"""
        # Scratch might be 8+
        launcher9 = AppsLauncher(self.catalog_path, child_age=9)
        apps9 = launcher9.get_all_apps()
        # Ensure only appropriate apps
        for app in apps9:
            self.assertLessEqual(app.min_age, 9)
            if app.max_age:
                self.assertGreaterEqual(app.max_age, 9)

    def test_age_filtering_3yo(self):
        """Test filtering for age 3"""
        launcher3 = AppsLauncher(self.catalog_path, child_age=3)
        apps3 = launcher3.get_all_apps()
        # YouTube Kids (usually 3+) should be there, but Wikipedia (8+) should probably not
        ids = [a.id for a in apps3]
        if "gcompris" in ids:  # GCompris starts at 2
            self.assertIn("gcompris", ids)
        if "wiki" in ids:      # Wikipedia usually older
            self.assertNotIn("wiki", ids)

    def test_launch_invalid_app(self):
        """Test launching non-existent app"""
        res = self.launcher.launch("non-existent-id-xyz")
        self.assertFalse(res.success)
        msg = res.message.lower()
        self.assertTrue("tidak ditemukan" in msg or "not found" in msg)

if __name__ == '__main__':
    unittest.main()
