# Hybrid LMS - Deployment Configuration

## Production Environment Setup

### 1. Environment Variables (.env.production)

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

### 2. System Requirements

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx (reverse proxy)
- SSL Certificate

### 3. Installation Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd hybridLms

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# 4. Environment setup
cp .env.example .env.production
# Edit .env.production with your values

# 5. Database setup
createdb hybrid_lms_production
python manage.py migrate
python manage.py collectstatic --noinput

# 6. Create superuser
python manage.py createsuperuser

# 7. Load initial data (optional)
python manage.py loaddata fixtures/categories.json
python manage.py loaddata fixtures/sample_courses.json
```

### 4. Gunicorn Configuration (gunicorn.conf.py)

```python
bind = "0.0.0.0:8000"
workers = 3
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 2
user = "hybridlms"
group = "hybridlms"
```

### 5. Nginx Configuration

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

### 6. Systemd Service (hybridlms.service)

```ini
[Unit]
Description=Hybrid LMS Django Application
After=network.target

[Service]
User=hybridlms
Group=hybridlms
WorkingDirectory=/path/to/hybridLms
ExecStart=/path/to/hybridLms/venv/bin/gunicorn --config gunicorn.conf.py hybrid_lms.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 7. Celery Configuration

#### Celery Worker Service (celery-worker.service)

```ini
[Unit]
Description=Hybrid LMS Celery Worker
After=network.target

[Service]
Type=forking
User=hybridlms
Group=hybridlms
WorkingDirectory=/path/to/hybridLms
ExecStart=/path/to/hybridLms/venv/bin/celery multi start worker1 \
    -A hybrid_lms --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO
ExecStop=/path/to/hybridLms/venv/bin/celery multi stopwait worker1 \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/path/to/hybridLms/venv/bin/celery multi restart worker1 \
    -A hybrid_lms --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8. Database Backup Script

```bash
#!/bin/bash
# backup_db.sh

DB_NAME="hybrid_lms_production"
DB_USER="hybrid_lms_user"
BACKUP_DIR="/backups/hybridlms"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/hybridlms_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/hybridlms_$DATE.sql

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: hybridlms_$DATE.sql.gz"
```

### 9. Monitoring and Logging

```python
# settings/production.py additional settings

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hybridlms/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/hybridlms/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'hybrid_lms': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 10. Performance Optimization

```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
```

### 11. Security Checklist

- [x] DEBUG = False
- [x] Strong SECRET_KEY
- [x] HTTPS enabled
- [x] Database credentials secured
- [x] File upload limits set
- [x] CORS properly configured
- [x] Regular security updates
- [x] Database backups automated
- [x] Error logging configured
- [x] Rate limiting implemented

### 12. Deployment Commands

```bash
# Deploy new version
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart hybridlms
sudo systemctl restart celery-worker
sudo systemctl reload nginx
```

### 13. Health Monitoring

Create a health check endpoint:

```python
# health/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

### 14. Load Balancing (if needed)

For high traffic, use multiple application servers:

```nginx
upstream hybridlms_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    # ... SSL configuration ...

    location / {
        proxy_pass http://hybridlms_backend;
        # ... other proxy settings ...
    }
}
```

This configuration provides a production-ready deployment setup for the Hybrid LMS system with scalability, security, and monitoring considerations.
