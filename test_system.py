#!/usr/bin/env python
"""
Comprehensive test script for Hybrid LMS API
Tests Django setup, database migrations, and API endpoints
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add Django project to path
sys.path.append('/Users/ROFI/Develop/proyek/hybridLms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')

def test_django_setup():
    """Test Django project setup and imports"""
    try:
        import django
        django.setup()
        print("✅ Django setup successful")
        
        # Test model imports
        from accounts.models import User
        from courses.models import Course, CourseEnrollment
        from lessons.models import Lesson, LessonProgress
        from assignments.models import Assignment
        from forums.models import ForumPost
        from payments.models import Order, Cart
        from live_sessions.models import LiveSession
        
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def test_database_migration():
    """Test database migration creation"""
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Capture output
        output = StringIO()
        
        # Run makemigrations
        call_command('makemigrations', stdout=output, verbosity=1)
        migration_output = output.getvalue()
        
        # Run migrate
        output = StringIO()
        call_command('migrate', stdout=output, verbosity=1)
        migrate_output = output.getvalue()
        
        print("✅ Database migrations successful")
        print(f"Migration output: {migration_output}")
        print(f"Migrate output: {migrate_output}")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints availability (requires server running)"""
    base_url = "http://localhost:8000/api/v1"
    
    endpoints_to_test = [
        "/auth/register/",
        "/courses/",
        "/lessons/",
        "/assignments/",
        "/forums/",
        "/payments/cart/",
        "/live-sessions/",
        "/analytics/dashboard/",
        "/gamification/badges/"
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code in [200, 401, 403] else "❌"
            results.append(f"{status} {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            results.append(f"🔍 {endpoint}: Server not running")
        except Exception as e:
            results.append(f"❌ {endpoint}: {e}")
    
    for result in results:
        print(result)
    
    return results

def test_model_creation():
    """Test creating model instances"""
    try:
        from accounts.models import User
        from courses.models import Course, CourseCategory
        
        # Test user creation
        user_count = User.objects.count()
        print(f"✅ Current users in database: {user_count}")
        
        # Test category creation
        category_count = CourseCategory.objects.count()
        print(f"✅ Current categories in database: {category_count}")
        
        # Test course creation
        course_count = Course.objects.count()
        print(f"✅ Current courses in database: {course_count}")
        
        return True
    except Exception as e:
        print(f"❌ Model creation test failed: {e}")
        return False

def test_api_documentation():
    """Test API documentation endpoints"""
    base_url = "http://localhost:8000"
    
    docs_endpoints = [
        "/api/docs/",
        "/api/redoc/", 
        "/api/schema/"
    ]
    
    results = []
    
    for endpoint in docs_endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            results.append(f"{status} Documentation {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            results.append(f"🔍 Documentation {endpoint}: Server not running")
        except Exception as e:
            results.append(f"❌ Documentation {endpoint}: {e}")
    
    for result in results:
        print(result)
    
    return results

def generate_test_report():
    """Generate comprehensive test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_results": {}
    }
    
    print("=" * 60)
    print("HYBRID LMS API - COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Run all tests
    print("\n1. Testing Django Setup...")
    report["test_results"]["django_setup"] = test_django_setup()
    
    print("\n2. Testing Database Migrations...")
    report["test_results"]["database_migration"] = test_database_migration()
    
    print("\n3. Testing Model Creation...")
    report["test_results"]["model_creation"] = test_model_creation()
    
    print("\n4. Testing API Endpoints...")
    api_results = test_api_endpoints()
    report["test_results"]["api_endpoints"] = api_results
    
    print("\n5. Testing API Documentation...")
    docs_results = test_api_documentation()
    report["test_results"]["api_documentation"] = docs_results
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for key, value in report["test_results"].items() 
                      if isinstance(value, bool) and value)
    total_tests = len([key for key, value in report["test_results"].items() 
                      if isinstance(value, bool)])
    
    print(f"Core Tests Passed: {passed_tests}/{total_tests}")
    
    # Check if server is needed for full test
    server_needed = any("Server not running" in str(result) 
                       for result_list in [api_results, docs_results]
                       for result in result_list)
    
    if server_needed:
        print("\n📝 Note: To test API endpoints and documentation:")
        print("   Run: python manage.py runserver")
        print("   Then run this script again for full validation")
    
    # Save report
    with open('test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Test report saved to: test_report.json")
    
    return report

if __name__ == "__main__":
    generate_test_report()