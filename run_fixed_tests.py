#!/usr/bin/env python
"""
Script to run the fixed tests and verify our fixes
"""
import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

from django.test.utils import get_runner
import unittest

def run_specific_tests():
    """Run specific tests that we've fixed"""
    # Import the test classes
    from analytics.tests import AnalyticsAPITest, AnalyticsServiceTest
    from role_management.tests import RoleRequestModelTest
    
    # Create a test suite with the specific tests we've fixed
    suite = unittest.TestSuite()
    
    # Add the tests that were failing
    suite.addTest(AnalyticsAPITest('test_platform_metrics_list_admin_only'))
    suite.addTest(AnalyticsAPITest('test_course_analytics_access_control'))
    suite.addTest(RoleRequestModelTest('test_unique_pending_request_constraint'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running fixed tests...")
    success = run_specific_tests()
    if success:
        print("\nAll fixed tests passed!")
    else:
        print("\nSome tests still failing.")
    sys.exit(0 if success else 1)