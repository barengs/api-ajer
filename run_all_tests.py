#!/usr/bin/env python
"""
Script to run all tests for the Hybrid LMS project
"""
import os
import sys
import django
import subprocess
from django.conf import settings

def run_django_tests():
    """Run all Django tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')
    
    try:
        # Setup Django
        django.setup()
        
        # Run tests using Django's test runner
        from django.core.management import execute_from_command_line
        print("Running all tests...")
        execute_from_command_line(['manage.py', 'test', '--settings=hybrid_lms.settings', '--verbosity=2'])
        return True
    except Exception as e:
        print(f"Error running Django tests: {e}")
        return False

def run_pytest_tests():
    """Run tests using pytest"""
    try:
        print("Running tests with pytest...")
        result = subprocess.run([sys.executable, '-m', 'pytest', '--verbose'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running pytest tests: {e}")
        return False

if __name__ == "__main__":
    print("Hybrid LMS Test Runner")
    print("=" * 30)
    
    # Try Django tests first
    success = run_django_tests()
    
    if not success:
        print("Django tests failed, trying pytest...")
        run_pytest_tests()
    
    print("Test execution completed.")