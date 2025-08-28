#!/usr/bin/env python
"""
Simple test runner to capture test output
"""
import os
import sys
import subprocess
import time

def run_test():
    """Run a simple test and capture output"""
    try:
        # Change to the project directory
        os.chdir('/Users/ROFI/Develop/proyek/hybridLms')
        
        # Run the test command
        cmd = [
            sys.executable, 'manage.py', 'test', 
            'analytics.tests.AnalyticsModelsTest.test_platform_metrics_creation',
            '--settings=hybrid_lms.settings',
            '--verbosity=2',
            '--keepdb'
        ]
        
        print("Running test command:", ' '.join(cmd))
        
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        # Write output to files
        with open('test_stdout.txt', 'w') as f:
            f.write(result.stdout)
        
        with open('test_stderr.txt', 'w') as f:
            f.write(result.stderr)
        
        print(f"Test completed with return code: {result.returncode}")
        print(f"STDOUT written to test_stdout.txt")
        print(f"STDERR written to test_stderr.txt")
        
        # Print summary
        if result.returncode == 0:
            print("Test PASSED")
        else:
            print("Test FAILED")
            
    except subprocess.TimeoutExpired:
        print("Test timed out after 60 seconds")
    except Exception as e:
        print(f"Error running test: {e}")

if __name__ == "__main__":
    run_test()