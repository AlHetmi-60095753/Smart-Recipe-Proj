import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-2.5-flash-lite"
API_ENDPOINT = (
    f"https://aiplatform.googleapis.com/v1/publishers/google/models/{MODEL}:generateContent"
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
