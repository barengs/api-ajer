# Panduan Instalasi Lengkap - Hybrid LMS

## 📋 Daftar Isi

1. [Persyaratan Sistem](#persyaratan-sistem)
2. [Instalasi untuk Development](#instalasi-untuk-development)
3. [Instalasi untuk Production](#instalasi-untuk-production)
4. [Konfigurasi Database](#konfigurasi-database)
5. [Konfigurasi Environment Variables](#konfigurasi-environment-variables)
6. [Instalasi Redis (Optional)](#instalasi-redis-optional)
7. [Setup Email (Optional)](#setup-email-optional)
8. [Setup Payment Gateway](#setup-payment-gateway)
9. [Troubleshooting](#troubleshooting)

## 📋 Persyaratan Sistem

### Minimum Requirements

- **Python**: 3.11 atau lebih baru
- **Database**: PostgreSQL 14+ (atau SQLite untuk development)
- **Memory**: 2GB RAM minimum (4GB direkomendasikan)
- **Storage**: 10GB free space minimum
- **OS**: Windows 10+, macOS 10.15+, atau Linux

### Optional Requirements

- **Redis**: 6+ (untuk caching dan background tasks)
- **Git**: Untuk version control
- **Node.js**: 16+ (jika menggunakan frontend terpisah)

## 🚀 Instalasi untuk Development

### 1. Persiapan Environment

#### Windows

```powershell
# Install Python dari python.org
# Install Git dari git-scm.com

# Verifikasi instalasi
python --version
git --version
```

#### macOS

```bash
# Install Homebrew (jika belum ada)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python dan Git
brew install python@3.11 git

# Verifikasi instalasi
python3 --version
git --version
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python, pip, dan Git
sudo apt install python3.11 python3.11-venv python3-pip git

# Verifikasi instalasi
python3 --version
git --version
```

### 2. Clone Repository

```bash
# Clone project dari GitHub
git clone https://github.com/your-username/hybrid-lms.git
cd hybrid-lms
```

### 3. Setup Virtual Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Verifikasi virtual environment aktif
which python  # macOS/Linux
where python   # Windows
```

### 4. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verifikasi instalasi
pip list
```

### 5. Setup Database (SQLite untuk Development)

```bash
# Jalankan migrations
python manage.py makemigrations
python manage.py migrate

# Buat superuser untuk admin
python manage.py createsuperuser
```

### 6. Setup Environment Variables

```bash
# Copy file .env example
cp .env.example .env

# Edit file .env
nano .env  # Linux/macOS
notepad .env  # Windows
```

### 7. Load Sample Data (Optional)

```bash
# Load sample data untuk testing
python manage.py loaddata fixtures/categories.json
python manage.py loaddata fixtures/sample_courses.json
```

### 8. Run Development Server

```bash
# Start development server
python manage.py runserver

# Server akan berjalan di http://127.0.0.1:8000/
```

## 🏭 Instalasi untuk Production

### 1. Setup Server (Ubuntu/CentOS)

#### Update System

```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu
sudo yum update -y  # CentOS
```

#### Install Dependencies

```bash
# Ubuntu
sudo apt install python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx git supervisor redis-server

# CentOS
sudo yum install python311 python3-pip postgresql postgresql-server nginx git supervisor redis
```

### 2. Setup PostgreSQL

#### Ubuntu

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Buat database dan user
sudo -u postgres psql
```

```sql
-- Di PostgreSQL console
CREATE DATABASE hybrid_lms;
CREATE USER hybrid_lms_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE hybrid_lms TO hybrid_lms_user;
ALTER USER hybrid_lms_user CREATEDB;
\q
```

#### CentOS

```bash
# Initialize database
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Konfigurasi authentication
sudo nano /var/lib/pgsql/data/pg_hba.conf
# Ubah 'ident' menjadi 'md5' untuk local connections

sudo systemctl restart postgresql
```

### 3. Setup Application

```bash
# Buat user untuk aplikasi
sudo adduser hybridlms
sudo su - hybridlms

# Clone repository
git clone https://github.com/your-username/hybrid-lms.git
cd hybrid-lms

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 4. Configure Environment Variables

```bash
# Buat file .env untuk production
nano .env
```

```env
# Production Environment Variables
DEBUG=False
SECRET_KEY=your-very-secret-key-here-change-this-in-production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=hybrid_lms
DB_USER=hybrid_lms_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=5432

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email (Gmail example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key

# AWS (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

### 5. Setup Database dan Static Files

```bash
# Database migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Buat superuser
python manage.py createsuperuser
```

### 6. Setup Gunicorn

```bash
# Test Gunicorn
gunicorn --bind 0.0.0.0:8000 hybrid_lms.wsgi

# Buat file konfigurasi Gunicorn
nano /home/hybridlms/hybrid-lms/gunicorn.conf.py
```

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
```

### 7. Setup Supervisor

```bash
sudo nano /etc/supervisor/conf.d/hybridlms.conf
```

```ini
[program:hybridlms]
command=/home/hybridlms/hybrid-lms/venv/bin/gunicorn --config /home/hybridlms/hybrid-lms/gunicorn.conf.py hybrid_lms.wsgi
directory=/home/hybridlms/hybrid-lms
user=hybridlms
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/hybridlms.log
```

```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start hybridlms
```

### 8. Setup Nginx

```bash
sudo nano /etc/nginx/sites-available/hybridlms
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/hybridlms/hybrid-lms/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/hybridlms/hybrid-lms/media/;
        expires 30d;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/hybridlms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🗄️ Konfigurasi Database

### PostgreSQL Production Setup

#### 1. Optimasi Performance

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```conf
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100

# Checkpoint settings
checkpoint_completion_target = 0.7
wal_buffers = 16MB
```

#### 2. Backup Setup

```bash
# Buat script backup
sudo nano /usr/local/bin/backup_hybridlms.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/backups/hybridlms"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U hybrid_lms_user -d hybrid_lms | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/hybridlms/hybrid-lms/media/

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

```bash
# Jadwalkan backup harian
sudo crontab -e
# Tambah line: 0 2 * * * /usr/local/bin/backup_hybridlms.sh
```

## 🔧 Konfigurasi Environment Variables

### Development (.env)

```env
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database (SQLite)
# DB_NAME akan otomatis menggunakan SQLite

# Email (Console backend untuk development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Payment (Test keys)
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key
STRIPE_SECRET_KEY=sk_test_your_test_key
```

### Production (.env)

```env
DEBUG=False
SECRET_KEY=super-secret-production-key-min-50-characters-long

# Database
DB_NAME=hybrid_lms
DB_USER=hybrid_lms_user
DB_PASSWORD=very-strong-password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=email-password

# Payment (Live keys)
STRIPE_PUBLISHABLE_KEY=pk_live_your_live_key
STRIPE_SECRET_KEY=sk_live_your_live_key

# Security
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🔄 Instalasi Redis (Optional)

### Ubuntu/Debian

```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
# Should return: PONG
```

### macOS

```bash
brew install redis
brew services start redis

# Test Redis
redis-cli ping
```

### Windows

```powershell
# Download dari https://github.com/microsoftarchive/redis/releases
# Install dan jalankan Redis service
```

### Setup Celery (Background Tasks)

```bash
# Dalam virtual environment
pip install celery[redis]

# Test Celery
celery -A hybrid_lms worker --loglevel=info
```

## 📧 Setup Email (Optional)

### Gmail Setup

1. Enable 2-Factor Authentication di akun Gmail
2. Generate App Password:
   - Google Account → Security → 2-Step Verification → App passwords
   - Select app: Mail, Device: Other (Custom name)
   - Copy password yang di-generate

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
```

### SendGrid Setup

```env
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=your-sendgrid-api-key
```

### Mailgun Setup

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=postmaster@yourdomain.com
EMAIL_HOST_PASSWORD=your-mailgun-smtp-password
```

## 💳 Setup Payment Gateway

### Stripe Setup

1. Daftar di https://stripe.com
2. Dapatkan API keys dari Dashboard:
   - Publishable key (pk*test*... atau pk*live*...)
   - Secret key (sk*test*... atau sk*live*...)

```env
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_here
```

### Test Payment

```bash
# Jalankan test payment
python manage.py test payments.tests.test_stripe_integration
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

```bash
# Fix file permissions
chmod +x manage.py
chown -R hybridlms:hybridlms /home/hybridlms/hybrid-lms/
```

#### 2. Database Connection Error

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l

# Test connection
python manage.py dbshell
```

#### 3. Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Celery Not Working

```bash
# Check Redis connection
redis-cli ping

# Test Celery connection
python -c "from celery import Celery; app = Celery('test'); app.config_from_object('django.conf:settings', namespace='CELERY'); print('Celery OK')"
```

#### 5. Memory Issues

```bash
# Check memory usage
free -h

# Restart services
sudo systemctl restart postgresql
sudo supervisorctl restart hybridlms
```

### Logs Location

```bash
# Application logs
tail -f /var/log/hybridlms.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# PostgreSQL logs
tail -f /var/log/postgresql/postgresql-14-main.log
```

### Performance Tuning

#### Database Optimization

```sql
-- Analyze database performance
ANALYZE;
VACUUM;

-- Check slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

#### Application Optimization

```bash
# Enable compression in Nginx
gzip on;
gzip_types text/plain application/json application/javascript text/css application/xml;

# Enable browser caching
expires 1d;
add_header Cache-Control "public, immutable";
```

## ✅ Verifikasi Instalasi

### Development

```bash
# Check semua services
python manage.py check
python manage.py test --keepdb

# Access aplikasi
curl http://127.0.0.1:8000/api/v1/
```

### Production

```bash
# Check system status
sudo systemctl status nginx
sudo systemctl status postgresql
sudo supervisorctl status
redis-cli ping

# Check aplikasi
curl https://yourdomain.com/api/v1/
```

## 📞 Bantuan Lebih Lanjut

Jika mengalami kesulitan:

1. Check [Troubleshooting](#troubleshooting) section
2. Baca log files untuk error details
3. Buat issue di GitHub repository
4. Hubungi tim support

---

**Selamat! Hybrid LMS siap digunakan! 🎉**
