import os
import re

from flask import Flask, request, jsonify, send_from_directory
from http import HTTPStatus
from typing import Any, Dict, List, Tuple

import ai

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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
