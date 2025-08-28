import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Try to import a simple model
from accounts.models import User

print("Django setup successful")
print(f"User model: {User}")