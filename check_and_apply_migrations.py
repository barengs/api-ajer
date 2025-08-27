import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

print("=== Checking current migration status ===")
try:
    call_command('showmigrations', verbosity=2)
except Exception as e:
    print(f"Error checking migrations: {e}")

print("\n=== Applying role_management migrations ===")
try:
    call_command('migrate', 'role_management', verbosity=2)
    print("Role management migrations applied successfully!")
except Exception as e:
    print(f"Error applying role_management migrations: {e}")

print("\n=== Applying navigation migrations ===")
try:
    call_command('migrate', 'navigation', verbosity=2)
    print("Navigation migrations applied successfully!")
except Exception as e:
    print(f"Error applying navigation migrations: {e}")

print("\n=== Final migration status ===")
try:
    call_command('showmigrations', verbosity=2)
except Exception as e:
    print(f"Error checking final migration status: {e}")