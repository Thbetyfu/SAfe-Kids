
import logging
import unittest
from pathlib import Path

# Add project root to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from safekid.content_filter.blocklist_manager import BlocklistManager, BlockCategory
from safekid.content_filter.filter_manager import ContentFilterManager

class TestContentFilter(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        self.mgr = BlocklistManager()
        self.mgr._domains_set = set() # Override any existing data

    def test_blocklist_manager_add_remove(self):
        """Test adding/removing domains"""
        self.mgr.add_domain("test-bad.com", "test")
        self.assertTrue(self.mgr.is_blocked("test-bad.com"))
        
        # Test subdomain
        self.assertTrue(self.mgr.is_blocked("www.test-bad.com"))
        self.assertFalse(self.mgr.is_blocked("test-good.com"))
        
        # Remove
        self.mgr.remove_domain("test-bad.com")
        self.assertFalse(self.mgr.is_blocked("test-bad.com"))

    def test_age_presets_manager(self):
        """Test age-based content filtering"""
        # Age 5
        cf5 = ContentFilterManager(age=5)
        cats5 = cf5.get_categories_for_age()
        self.assertIn(BlockCategory.ADULT, cats5)
        self.assertIn(BlockCategory.GAMBLING, cats5)
        self.assertIn(BlockCategory.VIOLENCE, cats5)

        # Age 14 (Teens) - Minimal filter
        cf14 = ContentFilterManager(age=14)
        cats14 = cf14.get_categories_for_age()
        self.assertIn(BlockCategory.ADULT, cats14)
        # Maybe allow violence/games? Check logic
        self.assertTrue(len(cats14) < len(cats5)) # Less restrictions

    def test_dry_run_flag(self):
        """Test dry-run mode on Windows"""
        import platform
        if platform.system() == "Windows":
            cf = ContentFilterManager(age=10)
            self.assertTrue(cf.dry_run)
            
            # Setup should pass without errors
            res = cf.setup(download_blocklists=False)
            self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()
