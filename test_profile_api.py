#!/usr/bin/env python
"""
Test script to verify profile endpoints are working correctly.
This script can be run independently to check if the profile endpoints are accessible.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def test_profile_endpoints():
    """Test that profile endpoints are properly configured"""
    print("Testing profile endpoint configuration...")
    
    try:
        from django.urls import reverse, resolve
        
        # Test URL resolution
        print("1. Testing URL resolution...")
        profile_url = reverse('user_profile')
        print(f"   ✓ Profile URL resolved: {profile_url}")
        
        profile_detail_url = reverse('user_profile_detail')
        print(f"   ✓ Profile detail URL resolved: {profile_detail_url}")
        
        # Test URL pattern resolution
        print("2. Testing URL pattern resolution...")
        profile_resolver = resolve('/api/v1/auth/profile/')
        print(f"   ✓ Profile URL pattern resolves to: {profile_resolver.view_name}")
        
        profile_detail_resolver = resolve('/api/v1/auth/profile/detail/')
        print(f"   ✓ Profile detail URL pattern resolves to: {profile_detail_resolver.view_name}")
        
        print("\n✅ All profile endpoints are properly configured!")
        print("\nAvailable endpoints:")
        print("  - GET/PUT /api/v1/auth/profile/ - Basic user profile")
        print("  - GET/PUT /api/v1/auth/profile/detail/ - Detailed user profile")
        print("\nTo use these endpoints:")
        print("  1. First authenticate using POST /api/v1/auth/login/")
        print("  2. Use the returned access token in the Authorization header")
        print("  3. Access the profile endpoints with Bearer token authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing profile endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_profile_endpoints()
    sys.exit(0 if success else 1)