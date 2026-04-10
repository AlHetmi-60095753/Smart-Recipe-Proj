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
