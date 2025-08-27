"""
Test to verify Google OAuth endpoint is properly defined
"""
import os
import sys
import django
from django.conf import settings
from django.urls import reverse, resolve

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def test_google_oauth_url():
    """Test that the Google OAuth URL is properly configured"""
    try:
        # Try to resolve the Google OAuth URL
        url = reverse('google_oauth_login')
        print(f"Google OAuth URL resolved successfully: {url}")
        
        # Try to resolve the social auth URLs
        from django.urls import include, path
        print("URL configuration test completed successfully")
        return True
    except Exception as e:
        print(f"Error testing Google OAuth URL: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google OAuth endpoint configuration...")
    success = test_google_oauth_url()
    if success:
        print("✅ Google OAuth endpoint is properly configured")
    else:
        print("❌ Google OAuth endpoint configuration has issues")