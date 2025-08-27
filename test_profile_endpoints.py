import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.urls import reverse, resolve

def test_profile_endpoints():
    """Test profile endpoints"""
    print("Testing profile endpoints...")
    
    try:
        # Test URL resolution for profile endpoints
        profile_url = reverse('user_profile')
        print(f"Profile URL: {profile_url}")
        
        profile_detail_url = reverse('user_profile_detail')
        print(f"Profile detail URL: {profile_detail_url}")
        
        # Test URL pattern resolution
        profile_resolver = resolve('/api/v1/auth/profile/')
        print(f"Profile URL resolves to: {profile_resolver.view_name}")
        
        profile_detail_resolver = resolve('/api/v1/auth/profile/detail/')
        print(f"Profile detail URL resolves to: {profile_detail_resolver.view_name}")
        
        print("All profile endpoints are properly configured!")
        
    except Exception as e:
        print(f"Error testing profile endpoints: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile_endpoints()