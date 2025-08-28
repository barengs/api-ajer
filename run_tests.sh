#!/bin/bash

# Simple test runner script for Hybrid LMS
# This script runs tests and generates a report

echo "Hybrid LMS Test Runner"
echo "======================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create a timestamp for the report
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="test_report_${TIMESTAMP}.txt"

echo "Running tests and saving output to ${REPORT_FILE}..."

# Run tests with verbosity and save output
python manage.py test --settings=hybrid_lms.settings --verbosity=2 --keepdb > "${REPORT_FILE}" 2>&1

# Check the exit code
if [ $? -eq 0 ]; then
    echo "Tests completed successfully!"
else
    echo "Tests completed with failures. Check ${REPORT_FILE} for details."
fi

echo "Test run completed at $(date)"
echo "Report saved to: ${REPORT_FILE}"