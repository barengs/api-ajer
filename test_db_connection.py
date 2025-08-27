import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Test database connection
from django.db import connection

try:
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Database connection successful!")
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
except Exception as e:
    print(f"Database connection failed: {e}")
    import traceback
    traceback.print_exc()