
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "database" / "edusmart.db"

new_columns = {
    "drive_file_id": "VARCHAR(255)",
    "drive_filename": "VARCHAR(255)",
    "drive_original_filename": "VARCHAR(255)",
    "drive_mime_type": "VARCHAR(150)",
}

connection = sqlite3.connect(DB_PATH)

try:
    cursor = connection.cursor()

    existing_columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(chapters)"
        ).fetchall()
    }

    if not existing_columns:
        raise RuntimeError(
            "Chapters table not found. Migration stopped."
        )

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE chapters ADD COLUMN "
                f"{column_name} {column_type}"
            )
            print(f"Added: {column_name}")
        else:
            print(f"Already exists: {column_name}")

    connection.commit()

    print("\nChapter migration completed successfully.")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
