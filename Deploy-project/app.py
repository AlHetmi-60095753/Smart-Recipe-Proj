import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

import ai
import db

load_dotenv()

app = Flask(__name__, static_folder="static")
# Make sure the database schema exists regardless of how the server is launched.
db.init_db()


def error_response(message: str, status: int = 400):
    """Return a tiny JSON error payload."""
    return jsonify({"error": message}), status


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/info")
def info():
    return jsonify({"student_id": os.environ.get("STUDENT_ID", "NOT SET")})


@app.route("/api/recipe/generate", methods=["POST"])
def generate_recipe():
    data = request.get_json(silent=True) or {}
    ingredients = data.get("ingredients", [])
    custom_name = data.get("custom_name", "")

    try:
        recipe = ai.generate_recipe(ingredients, custom_name=custom_name)
        return jsonify(recipe)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception:
        # Typically network/auth errors from the model provider; keep it simple for the UI.
        return error_response("Recipe service is unavailable. Please try again.", 503)


@app.route("/api/recipes/save", methods=["POST"])
def save_recipe():
    data = request.get_json(silent=True) or {}
    recipe_name = data.get("recipeName")
    if not recipe_name:
        return error_response("recipeName is required", 400)

    conn = db.get_connection()
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
    conn.close()
    return jsonify({"ok": True, "recipe_id": recipe_id})


@app.route("/api/recipes")
def list_recipes():
    conn = db.get_connection()
    rows = conn.execute(
        """
        SELECT id, recipe_name, input_mode, prompt_name, ingredients, cooking_time, servings, saved_at
        FROM recipes
        ORDER BY saved_at DESC, id DESC
        LIMIT 6
        """
    ).fetchall()
    conn.close()

    recipes = []
    for row in rows:
        item = dict(row)
        item["ingredients"] = json.loads(item["ingredients"])
        recipes.append(item)

    return jsonify(recipes)


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
