#!/bin/bash

# Hybrid LMS Deployment Script
# This script automates the deployment process for production

set -e  # Exit on any error

echo "Starting Hybrid LMS deployment..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Warning: Virtual environment not found. Proceeding without it."
fi

# Check if requirements-prod.txt exists
if [ -f "requirements-prod.txt" ]; then
    echo "Installing production requirements..."
    pip install -r requirements-prod.txt
else
    echo "Warning: requirements-prod.txt not found. Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=hybrid_lms.settings_prod

# Run migrations
echo "Applying database migrations..."
python manage.py migrate --settings=hybrid_lms.settings_prod

# Create cache table if needed
echo "Creating cache table if needed..."
python manage.py createcachetable --settings=hybrid_lms.settings_prod

# Compress static files
echo "Compressing static files..."
python manage.py compress --settings=hybrid_lms.settings_prod

# Restart services (this would typically be done with systemd or similar)
echo "Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Restart your web server (Gunicorn/Nginx)"
echo "2. Restart Celery workers if needed"
echo "3. Check application health at /api/v1/health/"

exit 0