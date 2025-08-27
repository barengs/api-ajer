#!/usr/bin/env python
import os
import sys

# Add the project directory to the Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')

try:
    import django
    print("Django imported successfully")
    
    # Setup Django
    django.setup()
    print("Django setup completed")
    
    # Try to import a simple model
    from django.contrib.auth.models import User
    print("Django User model imported successfully")
    
    # Try to get the count of users
    user_count = User.objects.count()
    print(f"Number of users in database: {user_count}")
    
    print("All tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()