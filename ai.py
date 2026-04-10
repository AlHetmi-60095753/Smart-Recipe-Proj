import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash-lite"
API_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)
PANTRY_STAPLES = ["salt", "pepper", "water", "oil"]

def _call(prompt: str) -> str:
    api_key = os.environ["GEMINI_KEY"]
    url = f"{API_ENDPOINT}?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
    }

    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=45,
    )
    response.raise_for_status()

    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]

def _clean_json(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _normalize_list(values: list[str]) -> list[str]:
    normalized = []
    for value in values:
        cleaned = value.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized

def generate_recipe(
    ingredients: list[str],
    custom_name: str = "",
    pantry_staples: list[str] | None = None,
) -> dict:
    pantry_staples = pantry_staples or PANTRY_STAPLES
    ingredients = _normalize_list(ingredients)

    if len(ingredients) != 5:
        raise ValueError("Exactly 5 ingredients are required.")

    custom_name = custom_name.strip()
    mode = "custom" if custom_name else "five-ingredients"

    prompt = f"""
You are generating a recipe for a student web app.

Rules:
- Use all 5 provided ingredients.
- Do not introduce any extra ingredients except these pantry staples: {json.dumps(pantry_staples)}.
- If an ingredient is not in the provided list or pantry staples, do not mention it.
- Keep the recipe practical and easy to follow.
- Return ONLY valid JSON with no markdown.

Input mode: {mode}
Recipe name request: {custom_name or "None"}
Provided ingredients: {json.dumps(ingredients)}

JSON format:
{{
  "recipeName": "string",
  "ingredientsUsed": ["string", "string"],
  "steps": ["string", "string", "string"],
  "cookingTime": "string",
  "servings": "string"
}}
"""

    recipe = json.loads(_clean_json(_call(prompt)))
    recipe["ingredientsUsed"] = _normalize_list(recipe.get("ingredientsUsed", []))
    recipe["steps"] = _normalize_list(recipe.get("steps", []))
    recipe["pantryStaples"] = pantry_staples
    recipe["inputMode"] = mode
    recipe["promptName"] = custom_name
    recipe["inputIngredients"] = ingredients
    return recipe
