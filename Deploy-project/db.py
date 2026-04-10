import sqlite3

DB_PATH = 'recipes.db'

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS recipes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_name      TEXT NOT NULL,
            input_mode       TEXT NOT NULL,
            prompt_name      TEXT,
            ingredients      TEXT NOT NULL,
            pantry_staples   TEXT NOT NULL,
            steps            TEXT NOT NULL,
            cooking_time     TEXT NOT NULL,
            servings         TEXT NOT NULL,
            saved_at         DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()
