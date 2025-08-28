import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("Successfully imported User model")
print("User model:", User)
print("User manager:", User.objects)
print("Has create_user:", hasattr(User.objects, 'create_user'))

# Try to create a user
try:
    user = User.objects.create_user(  # type: ignore
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    print("Successfully created user:", user)
except Exception as e:
    print("Error creating user:", e)