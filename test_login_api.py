#!/usr/bin/env python
"""
Test script to demonstrate the updated login API with user data.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def demonstrate_login_api():
    """Demonstrate the updated login API with user data"""
    print("Demonstrating updated login API...")
    
    try:
        from accounts.models import User
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create a test user
        print("1. Creating test user...")
        test_image = SimpleUploadedFile(
            name='test_profile.jpg',
            content=b'test image content for profile',
            content_type='image/jpeg'
        )
        
        user = User.objects.create_user(
            email='apiuser@example.com',
            username='apiuser',
            password='apipassword123',
            full_name='API Test User',
            role=User.UserRole.INSTRUCTOR,
            profile_image=test_image
        )
        print(f"   ✓ Created user: {user.email} ({user.role})")
        
        print("\n2. To test the login API, use the following curl command:")
        print("""
curl -X POST http://localhost:8000/api/v1/auth/login/ \\
     -H "Content-Type: application/json" \\
     -d '{
       "email": "apiuser@example.com",
       "password": "apipassword123"
     }'
        """)
        
        print("Expected response includes:")
        print("  - access: JWT access token")
        print("  - refresh: JWT refresh token")
        print("  - user: Object with id, email, full_name, role, profile_image")
        
        print("\n3. Example response:")
        print("""
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "apiuser@example.com",
    "full_name": "API Test User",
    "role": "instructor",
    "profile_image": "/media/profiles/test_profile.jpg"
  }
}
        """)
        
        # Clean up test user
        user.delete()
        print("✓ Cleaned up test user")
        
        print("\n✅ Login API demonstration complete!")
        print("\nThe updated authentication system now includes user data in the login response,")
        print("making it easier for frontend applications to access user information immediately")
        print("after authentication without additional API calls.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error demonstrating login API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demonstrate_login_api()
    sys.exit(0 if success else 1)