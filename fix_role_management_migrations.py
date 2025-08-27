"""
Script to fix role_management migrations issue
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def fix_migrations():
    """Fix the role_management migrations issue"""
    try:
        # First, let's check the current state
        print("Checking current migration status...")
        execute_from_command_line(['manage.py', 'showmigrations', 'role_management'])
        
        # Try to apply migrations
        print("Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate', 'role_management'])
        
    except Exception as e:
        print(f"Error during migration: {e}")
        
        # If that fails, let's try to fake the initial migration and then apply the rest
        try:
            print("Trying to fake initial migration...")
            execute_from_command_line(['manage.py', 'migrate', 'role_management', '0001', '--fake'])
            print("Applying remaining migrations...")
            execute_from_command_line(['manage.py', 'migrate', 'role_management'])
        except Exception as e2:
            print(f"Error during fake migration: {e2}")
            
            # Last resort: reset all migrations
            try:
                print("Resetting all migrations...")
                execute_from_command_line(['manage.py', 'migrate', 'role_management', 'zero'])
                print("Re-applying migrations...")
                execute_from_command_line(['manage.py', 'migrate', 'role_management'])
            except Exception as e3:
                print(f"Error during migration reset: {e3}")

if __name__ == "__main__":
    fix_migrations()