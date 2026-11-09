import sqlite3

DB_PATH = "database/edusmart.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

columns = [
    row[1]
    for row in cursor.execute(
        "PRAGMA table_info(users)"
    ).fetchall()
]

if "is_active" not in columns:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1
    """)
    print("is_active column added successfully.")
else:
    print("is_active column already exists.")

connection.commit()
connection.close()

print("Student status migration completed.")