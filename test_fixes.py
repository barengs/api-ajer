#!/usr/bin/env python
"""
Script to test our fixes for the failing tests
"""
import os
import sys
import django
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
django.setup()

import unittest
from analytics.tests import AnalyticsAPITest, AnalyticsModelsTest
from role_management.tests import RoleRequestModelTest

def run_fixed_tests():
    """Run the specific tests that we've fixed"""
    # Create a test suite with our fixed tests
    suite = unittest.TestSuite()
    
    # Add the tests that were failing
    suite.addTest(AnalyticsModelsTest('test_platform_metrics_creation'))
    suite.addTest(AnalyticsAPITest('test_course_analytics_access_control'))
    suite.addTest(AnalyticsAPITest('test_update_instructor_metrics_access_control'))
    suite.addTest(AnalyticsAPITest('test_update_platform_metrics_admin_only'))
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
            print(f"  {test}")
            print(f"  {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}")
            print(f"  {traceback}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Testing our fixes...")
    success = run_fixed_tests()
    if success:
        print("\nAll fixed tests passed!")
    else:
        print("\nSome tests still failing.")
    sys.exit(0 if success else 1)