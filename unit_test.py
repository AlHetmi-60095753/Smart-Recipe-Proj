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

class TestGenerateRecipe(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.app.test_client()
        self.valid_payload = {
            "ingredients": ["egg", "milk", "flour", "butter", "sugar"],
            "custom_name": "",
        }
        self.fake_recipe = {
            "recipeName": "Simple Pancakes",
            "ingredientsUsed": ["egg", "milk", "flour", "butter", "sugar"],
            "steps": ["Mix ingredients", "Cook on pan"],
            "cookingTime": "15 minutes",
            "servings": "2",
        }
 
    @patch("app.ai.generate_recipe")
    def test_generate_success(self, mock_gen):
        mock_gen.return_value = self.fake_recipe
        res = self.client.post(
            "/api/recipe/generate",
            json=self.valid_payload,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["recipeName"], "Simple Pancakes")
 
    @patch("app.ai.generate_recipe")
    def test_generate_passes_custom_name(self, mock_gen):
        mock_gen.return_value = self.fake_recipe
        payload = {**self.valid_payload, "custom_name": "My Pancakes"}
        self.client.post("/api/recipe/generate", json=payload)
        mock_gen.assert_called_once_with(
            self.valid_payload["ingredients"], custom_name="My Pancakes"
        )
 
    @patch("app.ai.generate_recipe", side_effect=ValueError("Exactly 5 ingredients are required."))
    def test_generate_returns_400_on_value_error(self, _):
        res = self.client.post(
            "/api/recipe/generate",
            json={"ingredients": ["egg"], "custom_name": ""},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())
 
    @patch("app.ai.generate_recipe", side_effect=RuntimeError("API down"))
    def test_generate_returns_500_on_unexpected_error(self, _):
        res = self.client.post("/api/recipe/generate", json=self.valid_payload)
        self.assertEqual(res.status_code, 500)
        self.assertIn("error", res.get_json())
 
    @patch("app.ai.generate_recipe")
    def test_generate_with_empty_body(self, mock_gen):
        """Missing JSON body should not crash — ingredients defaults to []."""
        mock_gen.side_effect = ValueError("Exactly 5 ingredients are required.")
        res = self.client.post("/api/recipe/generate", data="", content_type="application/json")
        self.assertEqual(res.status_code, 400)

class TestSaveRecipe(unittest.TestCase):
    def setUp(self):
        self.client = flask_app.app.test_client()
        self.valid_recipe = {
            "recipeName": "Simple Pancakes",
            "inputMode": "five-ingredients",
            "promptName": "",
            "ingredientsUsed": ["egg", "milk", "flour", "butter", "sugar"],
            "pantryStaples": ["salt", "pepper"],
            "steps": ["Mix", "Cook"],
            "cookingTime": "15 minutes",
            "servings": "2",
        }
 
    def _make_mock_conn(self, lastrowid=42):
        mock_cur = MagicMock()
        mock_cur.lastrowid = lastrowid
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cur
        return mock_conn
 
    @patch("app.db.get_connection")
    def test_save_success_returns_recipe_id(self, mock_get_conn):
        mock_get_conn.return_value = self._make_mock_conn(lastrowid=42)
        res = self.client.post("/api/recipes/save", json=self.valid_recipe)
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["recipe_id"], 42)
 
    @patch("app.db.get_connection")
    def test_save_missing_recipe_name_returns_400(self, mock_get_conn):
        payload = {**self.valid_recipe}
        del payload["recipeName"]
        res = self.client.post("/api/recipes/save", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())
        mock_get_conn.assert_not_called()
 
    @patch("app.db.get_connection")
    def test_save_db_error_returns_500(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB locked")
        mock_get_conn.return_value = mock_conn
        res = self.client.post("/api/recipes/save", json=self.valid_recipe)
        self.assertEqual(res.status_code, 500)
        self.assertIn("error", res.get_json())
 
    @patch("app.db.get_connection")
    def test_save_closes_connection_on_success(self, mock_get_conn):
        mock_conn = self._make_mock_conn()
        mock_get_conn.return_value = mock_conn
        self.client.post("/api/recipes/save", json=self.valid_recipe)
        mock_conn.close.assert_called_once()
 
    @patch("app.db.get_connection")
    def test_save_closes_connection_on_db_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB locked")
        mock_get_conn.return_value = mock_conn
        self.client.post("/api/recipes/save", json=self.valid_recipe)
        mock_conn.close.assert_called_once()
 
    @patch("app.db.get_connection")
    def test_save_serializes_lists_to_json(self, mock_get_conn):
        mock_conn = self._make_mock_conn()
        mock_get_conn.return_value = mock_conn
        self.client.post("/api/recipes/save", json=self.valid_recipe)
        call_args = mock_conn.execute.call_args[0][1]
        # ingredients and pantry_staples columns should be JSON strings
        self.assertEqual(json.loads(call_args[3]), self.valid_recipe["ingredientsUsed"])
        self.assertEqual(json.loads(call_args[4]), self.valid_recipe["pantryStaples"])
