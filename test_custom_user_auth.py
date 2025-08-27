#!/usr/bin/env python
"""
Test script to verify custom user authentication with full_name, role, and profile_image.
"""

import os
import sys
import django
from django.core.files.uploadedfile import SimpleUploadedFile
import time
from typing import cast

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def test_custom_user_auth():
    """Test custom user authentication with additional user data"""
    print("Testing custom user authentication...")
    
    try:
        from accounts.models import User
        from accounts.serializers import CustomTokenObtainPairSerializer
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Create a test user with unique email
        print("1. Creating test user...")
        # Use timestamp to ensure unique email
        timestamp = int(time.time())
        user_email = f'testauth{timestamp}@example.com'
        
        user = User.objects.create_user(
            email=user_email,
            username=f'testauth{timestamp}',
            password='testpassword123',
            full_name='Test Auth User',
            role=User.UserRole.STUDENT
            # Not adding profile_image to avoid PIL processing issues in test
        )
        print(f"   ✓ Created user: {user.email}")
        
        # Test token generation
        print("2. Testing token generation...")
        # Cast to RefreshToken to help type checker
        refresh = cast(RefreshToken, RefreshToken.for_user(user))
        access_token = str(refresh.access_token)
        print(f"   ✓ Generated access token: {access_token[:20]}...")
        
        # Test custom token serializer
        print("3. Testing custom token serializer...")
        # Call get_token on the class, not an instance
        token = CustomTokenObtainPairSerializer.get_token(user)
        
        # Check that custom claims are included
        assert 'email' in token
        assert 'role' in token
        assert 'full_name' in token
        assert 'profile_image' in token
        
        print(f"   ✓ Custom claims in token:")
        print(f"     - Email: {token['email']}")
        print(f"     - Role: {token['role']}")
        print(f"     - Full Name: {token['full_name']}")
        print(f"     - Profile Image: {token['profile_image']}")
        
        print("\n✅ Custom user authentication is working correctly!")
        print("\nToken payload includes:")
        print("  - email")
        print("  - role")
        print("  - full_name")
        print("  - profile_image")
        
        # Clean up test user
        user.delete()
        print("\n✓ Cleaned up test user")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing custom user authentication: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_custom_user_auth()
    sys.exit(0 if success else 1)