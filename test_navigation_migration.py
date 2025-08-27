import os
import sys
import django
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Apply migrations
from django.core.management import call_command

try:
    print("Applying navigation migrations...")
    call_command('migrate', 'navigation', verbosity=2)
    print("Navigation migrations applied successfully!")
except Exception as e:
    print(f"Error applying migrations: {e}")
    import traceback
    traceback.print_exc()