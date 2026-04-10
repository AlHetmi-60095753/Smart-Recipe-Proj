# AI Recipe Generator - Assignment 8

This project is a Flask-based AI recipe generator that creates a recipe from
exactly 5 ingredients. The generated recipe includes a recipe name, ingredients
used, step-by-step instructions, cooking time, and servings.

## Features

- Five-ingredient recipe generation
- Optional custom recipe name mode
- Gemini-powered recipe output
- SQLite recipe saving and recent recipe listing
- Responsive single-page interface based on the provided wireframe

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Docker

```bash
docker build -t ai-recipe-app .
docker run -d -p 5001:5000 --name ai-recipe-app --env-file .env ai-recipe-app
```

## Environment variables

| Variable | Purpose |
|---|---|
| `GEMINI_KEY` | Gemini API key used by the backend |
| `STUDENT_ID` | Student identifier shown in the UI |
