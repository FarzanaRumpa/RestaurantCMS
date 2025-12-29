"""
Script to add phone and created_by_id columns to users table
"""
import sqlite3

# Direct SQLite connection to avoid ORM issues
db_path = 'instance/restaurant_platform.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add phone column
    cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
    print("Added phone column")
except sqlite3.OperationalError as e:
    print(f"Phone column might already exist: {e}")

try:
    # Add created_by_id column
    cursor.execute("ALTER TABLE users ADD COLUMN created_by_id INTEGER")
    print("Added created_by_id column")
except sqlite3.OperationalError as e:
    print(f"Created_by_id column might already exist: {e}")

conn.commit()
conn.close()

print("Database schema updated successfully!")
print("Please restart the Flask application.")

