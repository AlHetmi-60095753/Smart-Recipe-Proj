# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Initialize the database schema during build
RUN python -c "import db; db.init_db()"

# Environment variable for the port
ENV PORT=5000

# Start the application (shell form so $PORT expands)
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app