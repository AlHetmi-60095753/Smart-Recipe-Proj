# AI Recipe Generator

A Flask-based web application that generates creative recipes from exactly 5 ingredients using Google's Gemini AI. The app creates detailed recipes with cooking instructions, time estimates, and serving sizes, while maintaining a SQLite database of previously generated recipes.


## Features

-  **AI-Powered Recipe Generation** - Creates unique recipes from exactly 5 ingredients
- **Custom Recipe Names** - Optional mode to specify your own recipe title
- **Gemini Integration** - Leverages Google Gemini API for intelligent recipe creation
-  **Recipe History** - Saves and retrieves previously generated recipes from SQLite
-  **Responsive UI** - Modern, single-page interface with intuitive controls
-  **Production Ready** - Includes Gunicorn WSGI server for deployment

## Prerequisites

- Python 3.9 or higher
- Google Gemini API key
- Docker (optional, for containerized deployment)

## Project Structure

```
Deploy-project/
├── app.py              # Flask application and route handlers
├── ai.py               # Gemini API integration
├── db.py               # SQLite database operations
├── query_db.py         # Database query utilities
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── README.md           # This file
└── static/
    ├── index.html      # Frontend HTML
    ├── app.js          # Frontend JavaScript logic
    └── styles.css      # Styling
```

## Getting Started

### Local Development

1. **Clone or navigate to the project directory:**
   ```bash
   cd Deploy-project
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the project root:
   ```
   GEMINI_KEY=your_gemini_api_key_here
   STUDENT_ID=your_student_id_here
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Access the app:**
   Open your browser and navigate to `http://localhost:5000`

### Docker Deployment

Build and run the application in a Docker container:

```bash
docker build -t ai-recipe-app .
docker run -d -p 5001:5000 --name ai-recipe-app --env-file .env ai-recipe-app
```

Access the app at `http://localhost:5001`

## API Endpoints

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/` | GET | Serves the main HTML interface | - |
| `/api/health` | GET | Health check endpoint | Returns `{"status": "ok"}` |
| `/api/info` | GET | Application information | Returns app metadata |
| `/static/<filename>` | GET | Serves static assets | CSS, JS, images |

## Environment Variables


Google Gemini API authentication key 
Student identifier displayed in the UI 

## Technology Stack

- **Backend:**  Python 3.x
- **Database:** 
- **AI Engine:** Google Gemini API
- **Frontend:** HTML5, CSS3, Vanilla JavaScript

