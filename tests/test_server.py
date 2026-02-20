
import json
import logging
import unittest
from pathlib import Path

# Add project root to sys.path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from safekid.kid_ui.launcher_server import app, STATE, LAUNCHER

class TestServerEndpoints(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        # Reset state defaults for testing
        STATE.child_name = "TestChild"
        STATE.child_age = 10
        STATE.total_minutes = 60
        STATE.used_seconds = 0
        STATE.stars = 0
        STATE.admin_pin = "1234"

    def test_index_page(self):
        """Test root / serving launcher.html"""
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"SafeKid Flash", r.data)

    def test_api_status(self):
        """Test /api/status returning child state"""
        r = self.client.get('/api/status')
        data = json.loads(r.data)
        self.assertEqual(data["child_name"], "TestChild")
        self.assertEqual(data["remaining_seconds"], 3600)  # 60 min * 60
        self.assertEqual(data["progress_pct"], 0.0)

    def test_api_apps_filtering(self):
        """Test /api/apps filtering by age/category"""
        r = self.client.get('/api/apps?cat=edu')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        # Check structure
        self.assertIn("apps", data)
        self.assertIn("categories", data)
        self.assertIsInstance(data["apps"], list)
        
        # If apps exist, ensure category matches
        if data["apps"]:
            for app in data["apps"]:
                self.assertEqual(app["category"], "edu")

    def test_api_launch_valid(self):
        """Test launching an app (mocked logic)"""
        payload = {"app_id": "gcompris", "name": "GCompris Test"}
        r = self.client.post('/api/launch', json=payload)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(data["ok"])
        self.assertEqual(STATE.stars, 1)  # Earned a star!

    def test_api_launch_invalid(self):
        """Test launch without app_id"""
        r = self.client.post('/api/launch', json={})
        self.assertEqual(r.status_code, 400)

    def test_api_admin_auth(self):
        """Test admin endpoints require PIN"""
        # No PIN: 403
        r = self.client.get('/api/admin/status')
        self.assertEqual(r.status_code, 403)
        
        # Wrong PIN: 403
        r = self.client.get('/api/admin/status', headers={'X-SafeKid-PIN': 'wrong'})
        self.assertEqual(r.status_code, 403)

        # Correct PIN: 200
        r = self.client.get('/api/admin/status', headers={'X-SafeKid-PIN': '1234'})
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["child_name"], "TestChild")

    def test_api_admin_set_time(self):
        """Test admin time controls"""
        headers = {'X-SafeKid-PIN': '1234'}
        
        # Add 10 mins
        r = self.client.post('/api/admin/set-time', 
                             headers=headers,
                             json={"add_minutes": 10})
        self.assertEqual(r.status_code, 200)
        # Should reduce used_seconds (technically could go negative if starting at 0, clipped to 0)
        self.assertEqual(STATE.used_seconds, 0) # clipped at 0

        # Set used = 30 mins
        STATE.used_seconds = 1800
        r = self.client.post('/api/admin/set-time', 
                             headers=headers,
                             json={"add_minutes": 10})
        self.assertEqual(STATE.used_seconds, 1200) # 30 - 10 = 20 mins used

if __name__ == '__main__':
    logging.disable(logging.CRITICAL) # Silence logs during test
    unittest.main()
