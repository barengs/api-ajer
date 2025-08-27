"""
Test file for Google OAuth implementation
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

# Test imports
try:
    from social_django.models import UserSocialAuth
    print("Social Django imported successfully")
except ImportError as e:
    print(f"Failed to import social_django: {e}")

try:
    from oauth.views import google_oauth_login
    print("Google OAuth view imported successfully")
except ImportError as e:
    print(f"Failed to import google_oauth_login: {e}")

try:
    from social_core.backends.google import GoogleOAuth2
    print("Google OAuth2 backend imported successfully")
except ImportError as e:
    print(f"Failed to import GoogleOAuth2: {e}")

print("Test completed")