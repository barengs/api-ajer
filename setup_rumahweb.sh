#!/bin/bash

# Setup script for initial deployment on Rumahweb hosting
# This script should be run on the Rumahweb server after the initial code deployment

set -e  # Exit on any error

echo "Setting up Hybrid LMS on Rumahweb..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install production requirements
echo "Installing production requirements..."
pip install -r requirements-prod.txt

# Check if .env file exists, if not create a template
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# Production Configuration
DEBUG=False
SECRET_KEY=your-super-secret-production-key-here-change-this-immediately
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (using SQLite for simplicity, but PostgreSQL recommended for production)
# DB_NAME=hybrid_lms_production
# DB_USER=hybrid_lms_user
# DB_PASSWORD=secure-database-password
# DB_HOST=localhost
# DB_PORT=5432

# Redis (if available)
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.your-email-provider.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=noreply@yourdomain.com
# EMAIL_HOST_PASSWORD=email-password

# Payment Gateway
# STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
# STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
EOF
    echo "Please edit the .env file with your actual configuration values."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=hybrid_lms.settings_rumahweb

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=hybrid_lms.settings_rumahweb

# Create cache table if needed
echo "Creating cache table if needed..."
python manage.py createcachetable --settings=hybrid_lms.settings_rumahweb

# Compress static files
echo "Compressing static files..."
python manage.py compress --settings=hybrid_lms.settings_rumahweb

echo "Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your actual configuration values"
echo "2. Create a superuser: python manage.py createsuperuser --settings=hybrid_lms.settings_rumahweb"
echo "3. Restart your application through cPanel"
echo "4. Test the application at your domain"

exit 0