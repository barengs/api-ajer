# Hybrid LMS Production Deployment Guide

This document provides instructions for deploying the Hybrid LMS application to a production environment.

## Prerequisites

1. Python 3.8+
2. PostgreSQL 12+
3. Redis 6+
4. Systemd (for service management)
5. Nginx (reverse proxy)
6. SSL Certificate

## Directory Structure

```
/path/to/hybridLms/
├── manage.py
├── hybrid_lms/
│   ├── settings.py
│   ├── settings_prod.py
│   └── ...
├── requirements.txt
├── requirements-prod.txt
├── gunicorn.conf.py
├── deploy.sh
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
# Create database
createdb hybrid_lms_production

# Run migrations
python manage.py migrate --settings=hybrid_lms.settings_prod

# Create superuser
python manage.py createsuperuser --settings=hybrid_lms.settings_prod

# Collect static files
python manage.py collectstatic --noinput --settings=hybrid_lms.settings_prod
```

### 6. Service Configuration

#### Application Service (Gunicorn)

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

#### Celery Worker Service

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

### 7. Nginx Configuration

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
        add_header Cache-Control "public, no-transform";
    }
}
```

### 8. Monitoring and Health Checks

The application includes built-in health check endpoints:

- Basic health check: `/api/v1/health/`
- Deep health check: `/api/v1/health/deep/`

These endpoints can be used for monitoring the application status.

## Deployment Automation

Use the provided deployment script to automate the deployment process:

```bash
./deploy.sh
```

This script will:

1. Install production requirements
2. Collect static files
3. Apply database migrations
4. Create cache tables
5. Compress static files

## Security Considerations

1. Always use HTTPS in production
2. Set strong SECRET_KEY
3. Configure proper ALLOWED_HOSTS
4. Use strong database credentials
5. Regularly update dependencies
6. Implement proper backup strategies
7. Monitor logs for suspicious activity

## Backup Strategy

Regular backups should be implemented for:

1. Database (PostgreSQL)
2. Media files
3. Configuration files

Example backup script for database:

```bash
#!/bin/bash
pg_dump -U hybrid_lms_user -h localhost hybrid_lms_production > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Troubleshooting

### Check Service Status

```bash
sudo systemctl status hybridlms.service
sudo systemctl status celery-worker.service
```

### View Logs

```bash
sudo journalctl -u hybridlms.service -f
sudo journalctl -u celery-worker.service -f
```

### Common Issues

1. **Permission errors**: Ensure the hybridlms user has proper permissions
2. **Database connection**: Verify database credentials and connectivity
3. **Static files not found**: Run collectstatic command
4. **Celery tasks not processing**: Check Redis connectivity

## Maintenance

Regular maintenance tasks include:

1. Updating dependencies
2. Applying security patches
3. Monitoring disk space
4. Reviewing logs
5. Testing backups
