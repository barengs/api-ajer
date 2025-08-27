import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
print(f"Database path: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"  {table[0]}")
    
    # Check if user_role_assignments table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_role_assignments';")
    table_exists = cursor.fetchone()
    
    if table_exists:
        print("\nuser_role_assignments table exists")
        # Get the schema of the table
        cursor.execute("PRAGMA table_info(user_role_assignments);")
        columns = cursor.fetchall()
        print("Columns in user_role_assignments:")
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
    else:
        print("\nuser_role_assignments table does not exist")
        
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")