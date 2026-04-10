import json
import unittest
from unittest.mock import MagicMock, patch
 
import app as flask_app
 
 
class TestHealthAndInfo(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.app.test_client()
 
    def test_health_returns_ok(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})
 
    def test_info_returns_student_id(self):
        with flask_app.app.test_client() as client:
            with patch.dict("os.environ", {"STUDENT_ID": "s123"}):
                res = client.get("/api/info")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["student_id"], "s123")
 
    def test_info_fallback_when_env_unset(self):
        with flask_app.app.test_client() as client:
            with patch.dict("os.environ", {}, clear=True):
                res = client.get("/api/info")
        self.assertEqual(res.get_json()["student_id"], "NOT SET")

