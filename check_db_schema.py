import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the user_role_assignments table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_role_assignments';")
table_exists = cursor.fetchone()

if table_exists:
    print("Table 'user_role_assignments' exists")
    # Get the schema of the table
    cursor.execute("PRAGMA table_info(user_role_assignments);")
    columns = cursor.fetchall()
    print("Columns in 'user_role_assignments':")
    for column in columns:
        print(f"  {column[1]} ({column[2]})")
else:
    print("Table 'user_role_assignments' does not exist")

conn.close()