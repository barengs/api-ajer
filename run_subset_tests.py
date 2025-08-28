import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hybrid_lms.settings'
    django.setup()
    
    # Run specific tests
    from django.test.utils import setup_test_environment
    setup_test_environment()
    
    from role_management.tests import RoleManagementAPITest
    from navigation.tests import NavigationModelTests
    from analytics.tests import AnalyticsServiceTest
    import unittest
    
    # Create a test suite with specific tests
    suite = unittest.TestSuite()
    
    # Add specific test methods
    suite.addTest(RoleManagementAPITest('test_user_role_assignment_api'))
    suite.addTest(NavigationModelTests('test_get_navigation_tree_authenticated'))
    suite.addTest(AnalyticsServiceTest('test_update_instructor_metrics'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
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