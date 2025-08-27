# Hybrid LMS Production Deployment Guide

This document provides instructions for deploying the Hybrid LMS application to a production environment.

## Prerequisites

1. Python 3.8+
2. PostgreSQL 12+ (recommended) or SQLite
3. Redis 6+ (optional but recommended)
4. Systemd (for service management) or cPanel/Passenger (for shared hosting)
5. Nginx (reverse proxy) or Apache
6. SSL Certificate

## Directory Structure

```
/path/to/hybridLms/
├── manage.py
├── hybrid_lms/
│   ├── settings.py
│   ├── settings_prod.py
│   └── settings_rumahweb.py
├── requirements.txt
├── requirements-prod.txt
├── gunicorn.conf.py
├── deploy.sh
├── setup_rumahweb.sh
├── passenger_wsgi.py
├── hybridlms.service
├── celery-worker.service
└── ...
```

## Installation Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd hybridLms
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements-prod.txt
```

### 4. Configure Environment Variables

Create a `.env.production` file with the following variables:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-super-secret-production-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database Configuration (PostgreSQL)
DB_NAME=hybrid_lms_production
DB_USER=hybrid_lms_user
DB_PASSWORD=secure-database-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=email-password

# Payment Gateway
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key

# File Storage (AWS S3)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Security
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 5. Database Setup

```bash
# Create database (if using PostgreSQL)
createdb hybrid_lms_production

# Run migrations
python manage.py migrate --settings=hybrid_lms.settings_prod

# Create superuser
python manage.py createsuperuser --settings=hybrid_lms.settings_prod

# Collect static files
python manage.py collectstatic --noinput --settings=hybrid_lms.settings_prod
```

## Deployment Options

### Option 1: VPS/Server Deployment (Traditional)

#### Service Configuration

##### Application Service (Gunicorn)

1. Copy the service file to systemd directory:

   ```bash
   sudo cp hybridlms.service /etc/systemd/system/
   ```

2. Edit the service file to match your paths:

   ```bash
   sudo nano /etc/systemd/system/hybridlms.service
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable hybridlms.service
   sudo systemctl start hybridlms.service
   ```

##### Celery Worker Service

1. Copy the service file to systemd directory:

   ```bash
   sudo cp celery-worker.service /etc/systemd/system/
   ```

2. Edit the service file to match your paths:

   ```bash
   sudo nano /etc/systemd/system/celery-worker.service
   ```

3. Create required directories:

   ```bash
   sudo mkdir -p /var/log/celery
   sudo mkdir -p /var/run/celery
   sudo chown hybridlms:hybridlms /var/log/celery
   sudo chown hybridlms:hybridlms /var/run/celery
   ```

4. Enable and start the service:
   ```bash
   sudo systemctl enable celery-worker.service
   sudo systemctl start celery-worker.service
   ```

#### Nginx Configuration

Create an Nginx configuration file:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/hybridLms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /path/to/hybridLms/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

### Option 2: Shared Hosting Deployment (Rumahweb/cPanel)

#### Initial Setup

1. **Login to cPanel**

   - Access your cPanel dashboard through the Rumahweb control panel

2. **Create Python Application**

   - Navigate to "Setup Python App" in the Software section
   - Click "Create Application"
   - Configure with these settings:
     - Python version: 3.11 (or latest available)
     - Application root: `/home/yourusername/hybridlms`
     - Application URL: Select your domain
     - Leave other fields blank (Passenger will auto-configure)

3. **Upload Application Files**

   - Use the File Manager in cPanel or SCP/SFTP to upload your application files
   - Upload all files to the application root directory

4. **Run Setup Script**

   ```bash
   cd /home/yourusername/hybridlms
   chmod +x setup_rumahweb.sh
   ./setup_rumahweb.sh
   ```

5. **Configure Environment Variables**

   - Edit the `.env` file with your actual configuration values
   - Make sure to set a strong SECRET_KEY and configure ALLOWED_HOSTS

6. **Create Superuser**

   ```bash
   python manage.py createsuperuser --settings=hybrid_lms.settings_rumahweb
   ```

7. **Restart Application**
   - In cPanel, go to "Setup Python App"
   - Find your application and click the "Restart" button

#### Auto Deployment with GitHub Actions

See `AUTO_DEPLOYMENT.md` for detailed instructions on setting up automatic deployment from GitHub to Rumahweb hosting.

## Monitoring and Maintenance

### Health Checks

The application includes built-in health check endpoints:

- Basic health check: `/api/v1/health/`
- Detailed health check: `/api/v1/health/detail/`

### Log Management

Logs are configured to be written to:

- Application logs: `/path/to/hybridLms/django.log`
- Gunicorn logs: `/var/log/hybridlms/gunicorn-*.log`
- Celery logs: `/var/log/celery/*.log`

### Backup Strategy

Regular backups should include:

1. Database backups
2. Media files (user uploads)
3. Configuration files
4. SSL certificates

### Updates and Maintenance

To update the application:

1. Pull the latest code from the repository
2. Install/update dependencies:
   ```bash
   pip install -r requirements-prod.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate --settings=hybrid_lms.settings_prod
   ```
4. Collect static files:
   ```bash
   python manage.py collectstatic --noinput --settings=hybrid_lms.settings_prod
   ```
5. Restart services:
   ```bash
   sudo systemctl restart hybridlms
   sudo systemctl restart celery-worker
   ```

## Troubleshooting

### Common Issues

1. **Application Not Starting**

   - Check the Passenger error logs in cPanel
   - Verify the `passenger_wsgi.py` file is correctly configured
   - Ensure all required environment variables are set

2. **Database Connection Issues**

   - Verify database credentials in the `.env` file
   - Check if the database server is running
   - Ensure the database user has proper permissions

3. **Static Files Not Loading**

   - Run `collectstatic` command
   - Check file permissions on the static files directory
   - Verify Nginx/Apache configuration for static files

4. **Permission Errors**
   - Ensure the web server user has read permissions on application files
   - Check that the database user has proper permissions
   - Verify directory permissions for media and static files

### Debugging Commands

```bash
# Check application status
sudo systemctl status hybridlms

# View application logs
tail -f /var/log/hybridlms/gunicorn-error.log

# Test database connection
python manage.py dbshell --settings=hybrid_lms.settings_prod

# Run health checks
curl http://localhost:8000/api/v1/health/

# Check for pending migrations
python manage.py showmigrations --settings=hybrid_lms.settings_prod
```

## Security Considerations

1. **Secrets Management**

   - Never commit sensitive information to the repository
   - Use environment variables for all sensitive configuration
   - Rotate secrets regularly

2. **Access Control**

   - Use strong, unique passwords for all accounts
   - Implement proper user authentication and authorization
   - Regularly review user permissions

3. **Network Security**

   - Use HTTPS for all communications
   - Implement proper firewall rules
   - Regularly update system and application software

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Implement proper backup and recovery procedures
   - Regularly test backup restoration procedures
