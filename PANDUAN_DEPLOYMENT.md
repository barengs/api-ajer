# Panduan Deployment - Hybrid LMS

## 📋 Daftar Isi

1. [Persiapan Deployment](#persiapan-deployment)
2. [Deployment ke VPS/Server](#deployment-ke-vpsserver)
3. [Deployment dengan Docker](#deployment-dengan-docker)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Monitoring dan Security](#monitoring-dan-security)
6. [Troubleshooting](#troubleshooting)

## 🚀 Persiapan Deployment

### Environment Requirements

- **CPU**: 2+ vCPU
- **RAM**: 4GB+
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.11+
- **Database**: PostgreSQL 14+
- **Cache**: Redis 6+

### Pre-deployment Checklist

- [ ] Domain name configured
- [ ] SSL certificate ready
- [ ] Database server setup
- [ ] Redis server for caching
- [ ] Email service configured
- [ ] Payment gateway credentials
- [ ] Monitoring tools setup

## 🖥️ Deployment ke VPS/Server

### 1. Setup Server (Ubuntu 22.04)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip postgresql postgresql-contrib redis-server nginx git

# Setup PostgreSQL
sudo -u postgres psql
```

```sql
CREATE DATABASE hybrid_lms;
CREATE USER hybrid_lms_user WITH PASSWORD 'strong_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hybrid_lms TO hybrid_lms_user;
ALTER USER hybrid_lms_user CREATEDB;
\q
```

### 2. Setup Application

```bash
# Create application user
sudo adduser hybridlms
sudo su - hybridlms

# Clone project
git clone https://github.com/your-username/hybrid-lms.git
cd hybrid-lms

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3. Configure Environment Variables

```bash
nano .env
```

```env
# Production Configuration
DEBUG=False
SECRET_KEY=your-super-secret-production-key-50-characters-minimum
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=hybrid_lms
DB_USER=hybrid_lms_user
DB_PASSWORD=strong_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key

# Payment
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

### 4. Setup Database dan Static Files

```bash
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Configure Gunicorn

```bash
nano gunicorn_config.py
```

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
```

### 6. Setup Systemd Service

```bash
sudo nano /etc/systemd/system/hybridlms.service
```

```ini
[Unit]
Description=HybridLMS Django Application
After=network.target

[Service]
User=hybridlms
Group=www-data
WorkingDirectory=/home/hybridlms/hybrid-lms
Environment=PATH=/home/hybridlms/hybrid-lms/venv/bin
ExecStart=/home/hybridlms/hybrid-lms/venv/bin/gunicorn --config gunicorn_config.py hybrid_lms.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable hybridlms
sudo systemctl start hybridlms
sudo systemctl status hybridlms
```

### 7. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/hybridlms
```

```nginx
upstream hybridlms {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    client_max_body_size 100M;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Main Application
    location / {
        proxy_pass http://hybridlms;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static Files
    location /static/ {
        alias /home/hybridlms/hybrid-lms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /home/hybridlms/hybrid-lms/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

```bash
# Enable site and setup SSL
sudo ln -s /etc/nginx/sites-available/hybridlms /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Restart Nginx
sudo systemctl restart nginx
```

## 🐳 Deployment dengan Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE hybrid_lms.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hybrid_lms.wsgi:application"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: hybrid_lms
      POSTGRES_USER: hybridlms_user
      POSTGRES_PASSWORD: secure_password

  redis:
    image: redis:7-alpine

  celery:
    build: .
    command: celery -A hybrid_lms worker --loglevel=info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Deploy dengan Docker

```bash
# Build and deploy
docker-compose up --build -d

# Setup database
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Monitor logs
docker-compose logs -f web
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python manage.py test

  deploy:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.PRIVATE_KEY }}
          script: |
            cd /home/hybridlms/hybrid-lms
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart hybridlms
```

## 📊 Monitoring dan Security

### Health Checks

```python
# Install django-health-check
pip install django-health-check

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'health_check',
    'health_check.db',
    'health_check.cache',
]

# Add to urls.py
urlpatterns = [
    path('health/', include('health_check.urls')),
]
```

### Security Configuration

```python
# settings.py security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Backup Script

```bash
#!/bin/bash
# /usr/local/bin/backup_hybridlms.sh

BACKUP_DIR="/home/backups/hybridlms"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U hybrid_lms_user -d hybrid_lms | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/hybridlms/hybrid-lms/media/

# Clean up old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Setup cron job
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_hybridlms.sh
```

## 🚨 Troubleshooting

### Common Issues

#### 502 Bad Gateway

```bash
# Check Gunicorn status
sudo systemctl status hybridlms

# Check logs
sudo journalctl -u hybridlms -f

# Restart services
sudo systemctl restart hybridlms
```

#### Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U hybrid_lms_user -d hybrid_lms
```

#### High Memory Usage

```bash
# Monitor processes
top -o %MEM

# Check Gunicorn workers
ps aux | grep gunicorn

# Restart if needed
sudo systemctl restart hybridlms
```

### Emergency Procedures

#### Quick Rollback

```bash
cd /home/hybridlms/hybrid-lms
git reset --hard HEAD~1
sudo systemctl restart hybridlms
```

#### Database Recovery

```bash
# Stop application
sudo systemctl stop hybridlms

# Restore database
gunzip -c db_backup.sql.gz | psql -h localhost -U hybrid_lms_user -d hybrid_lms

# Start application
sudo systemctl start hybridlms
```

## 📞 Support dan Maintenance

### Regular Maintenance Tasks

#### Weekly

- [ ] Check application logs
- [ ] Monitor disk space
- [ ] Verify backups
- [ ] Check SSL certificate status

#### Monthly

- [ ] Update system packages
- [ ] Update Python dependencies
- [ ] Database maintenance (VACUUM, ANALYZE)
- [ ] Review security logs

### Monitoring Checklist

- [ ] Application uptime monitoring
- [ ] Database performance monitoring
- [ ] SSL certificate expiry alerts
- [ ] Disk space monitoring
- [ ] Memory usage monitoring
- [ ] Error rate monitoring
- [ ] Response time monitoring

### Contact Information

- **Technical Support**: tech@hybridlms.com
- **Emergency Hotline**: +62-xxx-xxxx-xxxx
- **Documentation**: https://docs.hybridlms.com

---

**🎉 Selamat! Hybrid LMS telah berhasil di-deploy dan siap digunakan!**

Pastikan untuk melakukan monitoring secara berkala dan mengikuti best practices untuk keamanan dan performa optimal.
