#!/usr/bin/env python
"""
Script to verify that our test fixes are working correctly
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

def test_analytics_imports():
    """Test that analytics imports work correctly"""
    try:
        # Test that we can import the analytics views
        from analytics.views import CourseAnalyticsView
        print("✅ Analytics views import successful")
        
        # Test that we can import the analytics models
        from analytics.models import PlatformMetrics, InstructorMetrics
        print("✅ Analytics models import successful")
        
        # Test that we can import the analytics services
        from analytics.services import AnalyticsService
        print("✅ Analytics services import successful")
        
        return True
    except Exception as e:
        print(f"❌ Analytics imports failed: {e}")
        return False

def test_role_management_imports():
    """Test that role management imports work correctly"""
    try:
        # Test that we can import the role management models
        from role_management.models import RoleDefinition, UserRoleAssignment
        print("✅ Role management models import successful")
        
        # Test that we can import the role management services
        from role_management.services import RoleManagementService
        print("✅ Role management services import successful")
        
        return True
    except Exception as e:
        print(f"❌ Role management imports failed: {e}")
        return False

def test_courses_imports():
    """Test that courses imports work correctly"""
    try:
        # Test that we can import the courses models
        from courses.models import Course
        print("✅ Courses models import successful")
        
        return True
    except Exception as e:
        print(f"❌ Courses imports failed: {e}")
        return False

def main():
    """Main function to run all verification tests"""
    print("=" * 60)
    print("HYBRID LMS - TEST FIXES VERIFICATION")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Analytics Imports", test_analytics_imports),
        ("Role Management Imports", test_role_management_imports),
        ("Courses Imports", test_courses_imports),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! The fixes appear to be working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())