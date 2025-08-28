#!/usr/bin/env python
"""
Comprehensive test runner for Hybrid LMS project
This script will run tests for each module and generate a report
"""
import os
import sys
import subprocess
import json
from datetime import datetime

# List of modules to test
MODULES = [
    'accounts',
    'analytics',
    'assignments',
    'courses',
    'forums',
    'gamification',
    'lessons',
    'live_sessions',
    'navigation',
    'notifications',
    'payments',
    'role_management',
    'oauth',
    'recommendations'
]

def run_module_tests(module_name):
    """Run tests for a specific module"""
    print(f"Running tests for module: {module_name}")
    
    cmd = [
        sys.executable, 'manage.py', 'test',
        f'{module_name}.tests',
        '--settings=hybrid_lms.settings',
        '--verbosity=1',
        '--keepdb'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per module
        )
        
        # Parse the output to get test results
        output = result.stdout + result.stderr
        lines = output.split('\n')
        
        # Look for test summary lines
        tests_run = 0
        failures = 0
        errors = 0
        
        for line in lines:
            if 'Ran' in line and 'test' in line and 'in' in line:
                # Extract number of tests run
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'Ran':
                        try:
                            tests_run = int(parts[i+1])
                        except (ValueError, IndexError):
                            pass
                        break
            
            if 'FAILED' in line and '(' in line:
                # Extract failures and errors
                parts = line.replace('(', '').replace(')', '').replace(',', '').split()
                for i, part in enumerate(parts):
                    if part == 'failures=':
                        try:
                            failures = int(parts[i+1])
                        except (ValueError, IndexError):
                            pass
                    elif part == 'errors=':
                        try:
                            errors = int(parts[i+1])
                        except (ValueError, IndexError):
                            pass
        
        return {
            'module': module_name,
            'success': result.returncode == 0,
            'return_code': result.returncode,
            'tests_run': tests_run,
            'failures': failures,
            'errors': errors,
            'stdout': result.stdout[:1000],  # Limit output size
            'stderr': result.stderr[:1000]   # Limit output size
        }
    except subprocess.TimeoutExpired:
        return {
            'module': module_name,
            'success': False,
            'error': 'TIMEOUT',
            'message': 'Test timed out after 120 seconds'
        }
    except Exception as e:
        return {
            'module': module_name,
            'success': False,
            'error': 'EXCEPTION',
            'message': str(e)
        }

def generate_report(results):
    """Generate a comprehensive test report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_modules': len(results),
        'successful_modules': len([r for r in results if r.get('success', False)]),
        'failed_modules': len([r for r in results if not r.get('success', True)]),
        'total_tests_run': sum(r.get('tests_run', 0) for r in results),
        'total_failures': sum(r.get('failures', 0) for r in results),
        'total_errors': sum(r.get('errors', 0) for r in results),
        'module_results': results
    }
    
    return report

def main():
    """Main function to run all tests and generate report"""
    print("Hybrid LMS Comprehensive Test Runner")
    print("=" * 50)
    print(f"Starting test run at {datetime.now()}")
    print(f"Testing {len(MODULES)} modules")
    print()
    
    # Change to project directory
    os.chdir('/Users/ROFI/Develop/proyek/hybridLms')
    
    # Run tests for each module
    results = []
    for module in MODULES:
        try:
            result = run_module_tests(module)
            results.append(result)
            print(f"Completed {module}: {'PASS' if result.get('success', False) else 'FAIL'}")
        except Exception as e:
            print(f"Error running tests for {module}: {e}")
            results.append({
                'module': module,
                'success': False,
                'error': 'RUNNER_ERROR',
                'message': str(e)
            })
    
    # Generate report
    report = generate_report(results)
    
    # Save report to file
    with open('comprehensive_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print()
    print("=" * 50)
    print("TEST RUN SUMMARY")
    print("=" * 50)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total modules tested: {report['total_modules']}")
    print(f"Successful modules: {report['successful_modules']}")
    print(f"Failed modules: {report['failed_modules']}")
    print(f"Total tests run: {report['total_tests_run']}")
    print(f"Total failures: {report['total_failures']}")
    print(f"Total errors: {report['total_errors']}")
    
    print()
    print("Module Details:")
    for result in report['module_results']:
        status = "PASS" if result.get('success', False) else "FAIL"
        tests_run = result.get('tests_run', 0)
        failures = result.get('failures', 0)
        errors = result.get('errors', 0)
        print(f"  {result['module']}: {status} ({tests_run} tests, {failures} failures, {errors} errors)")
    
    print()
    print("Detailed report saved to: comprehensive_test_report.json")
    
    # Return appropriate exit code
    if report['total_failures'] > 0 or report['total_errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()