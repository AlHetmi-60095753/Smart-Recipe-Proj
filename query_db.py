import sqlite3


def main() -> None:
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()

    print("=== TABLES ===")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for table in tables:
        print(f"  - {table[0]}")

    print("\n=== SCHEMA ===")
    for table in tables:
        table_name = table[0]
        columns = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        print(f"\n{table_name}:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")

    print("\n=== DATA ===")
    for table in tables:
        table_name = table[0]
        rows = cursor.execute(f"SELECT * FROM {table_name};").fetchall()
        print(f"\n{table_name} ({len(rows)} rows):")
        for row in rows[:3]:
            print(f"  {row}")

    conn.close()


if __name__ == "__main__":
    main()
