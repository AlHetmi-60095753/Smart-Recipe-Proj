import os
import re
import json

from flask import Flask, request, jsonify, send_from_directory
from http import HTTPStatus
from typing import Any, Dict, List, Tuple

import ai
import db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='static')


# ── Static files ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


# ── Student info (powers the footer) ──────────────────────────────────────────
@app.route('/api/info')
def info():
    return jsonify({'student_id': os.environ.get('STUDENT_ID', 'NOT SET')})


# ── Ingredient parsing helpers ────────────────────────────────────────────────
def normalize_ingredient(value: Any) -> str:
    """
    Clean up one ingredient value coming from the front-end.
    """
    if value is None:
        return ''
    text = str(value).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def split_ingredients_text(text: str) -> List[str]:
    """
    Split a comma-separated ingredient string into a list.
    Example: "a, b, c" -> ["a", "b", "c"]
    """
    if not text:
        return []
    parts = [p.strip() for p in text.split(',')]
    return [p for p in parts if p]


def extract_ingredients_from_payload(payload: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """
    Extract ingredients from the front-end payload.

    Returns:
    - ingredients: list of ingredient strings
    - errors: list of error messages (empty list means "valid")
    """
    mode = normalize_ingredient(payload.get('mode')).lower()
    errors: List[str] = []

    # For Custom mode.
    if mode == 'custom':
        raw = normalize_ingredient(payload.get('recipeIdea'))
        ingredients = [normalize_ingredient(x) for x in split_ingredients_text(raw)]
        if not ingredients:
            errors.append('Please enter at least 1 ingredient in the Ingredients List field.')
        return ingredients, errors

    # For 5 ingredient mode
    if mode in ('5', 'five', '5ingredients', '5-ingredients', ''):
        raw_list = payload.get('ingredients') or []
        if not isinstance(raw_list, list):
            errors.append('ingredients must be a list.')
            return [], errors

        ingredients = [normalize_ingredient(x) for x in raw_list]
        ingredients = [x for x in ingredients if x]

        if len(ingredients) != 5:
            errors.append('Please enter exactly 5 ingredients.')
        return ingredients, errors

    errors.append("mode must be either 'custom' or '5'.")
    return [], errors


def api_extract_ingredients(payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Turn ingredient extraction into a consistent JSON API response.
    """
    ingredients, errors = extract_ingredients_from_payload(payload)
    if errors:
        return HTTPStatus.BAD_REQUEST, {'ok': False, 'errors': errors, 'ingredients': []}
    return HTTPStatus.OK, {'ok': True, 'errors': [], 'ingredients': ingredients}


# ── Ingredient API (front-end calls this) ─────────────────────────────────────
@app.route('/api/ingredients', methods=['POST'])
def ingredients_api():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'ok': False, 'errors': ['Invalid JSON body.'], 'ingredients': []}), 400

    status, body = api_extract_ingredients(data)
    return jsonify(body), int(status)


@app.route("/api/recipe/generate", methods=["POST"])
def generate_recipe():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body."}), 400

    # Support both payload styles:
    # - Old: { ingredients: [...], custom_name: "..." }
    # - Current mode-based: { mode: "5"|"custom", ingredients: [...], recipeName, recipeIdea }
    custom_name = normalize_ingredient(data.get("custom_name")) or normalize_ingredient(
        data.get("recipeName")
    )

    if isinstance(data.get("ingredients"), list):
        ingredients = [normalize_ingredient(x) for x in (data.get("ingredients") or [])]
        ingredients = [x for x in ingredients if x]
        if len(ingredients) != 5:
            return jsonify({"error": "Please enter exactly 5 ingredients."}), 400
    else:
        ingredients, errors = extract_ingredients_from_payload(data)
        if errors:
            # Keep this endpoint's error shape compatible with the older front-end.
            return jsonify({"error": errors[0]}), 400

        if len(ingredients) != 5:
            return jsonify({"error": "Please enter exactly 5 ingredients."}), 400

    try:
        recipe = ai.generate_recipe(ingredients, custom_name=custom_name)
        return jsonify(recipe)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/recipes/save", methods=["POST"])
def save_recipe():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "Invalid JSON body."}), 400

    # Keep this aligned with the recipe JSON coming from ai.generate_recipe()
    try:
        recipe_name = str(data["recipeName"]).strip()
    except Exception:
        return jsonify({"ok": False, "error": "recipeName is required."}), 400

    conn = db.get_connection()
    try:
        try:
            cur = conn.execute(
                """
                INSERT INTO recipes (
                    recipe_name,
                    input_mode,
                    prompt_name,
                    ingredients,
                    pantry_staples,
                    steps,
                    cooking_time,
                    servings
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recipe_name,
                    data.get("inputMode", "five-ingredients"),
                    data.get("promptName", ""),
                    json.dumps(data.get("ingredientsUsed", [])),
                    json.dumps(data.get("pantryStaples", [])),
                    json.dumps(data.get("steps", [])),
                    data.get("cookingTime", ""),
                    data.get("servings", ""),
                ),
            )
            conn.commit()
            recipe_id = cur.lastrowid
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"ok": True, "recipe_id": recipe_id})


@app.route("/api/recipes")
def list_recipes():
    conn = db.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, recipe_name, input_mode, prompt_name, ingredients, cooking_time, servings, saved_at
            FROM recipes
            ORDER BY saved_at DESC, id DESC
            LIMIT 6
            """
        ).fetchall()
    finally:
        conn.close()

    recipes = []
    for row in rows:
        item = dict(row)
        try:
            item["ingredients"] = json.loads(item["ingredients"])
        except (json.JSONDecodeError, ValueError):
            item["ingredients"] = []
        recipes.append(item)

    return jsonify(recipes)


if __name__ == '__main__':
    db.init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

#TEST COMMENT

#Presentation Test Commit