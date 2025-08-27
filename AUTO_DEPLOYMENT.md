# Auto Deployment Setup for Hybrid LMS

This document explains how to set up automatic deployment of the Hybrid LMS application to Rumahweb hosting using GitHub Actions.

## Prerequisites

1. GitHub repository for your project
2. Rumahweb hosting account with Python support
3. SSH access to your Rumahweb hosting account
4. Domain configured in cPanel

## Setup Instructions

### 1. Configure Rumahweb Hosting

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

3. **Note the Virtual Environment Path**
   - After creating the application, cPanel will show a command to activate the virtual environment
   - Copy this path as you'll need it for deployment

### 2. Configure GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions and add these secrets:

| Secret Name        | Description                  | Example Value                            |
| ------------------ | ---------------------------- | ---------------------------------------- |
| `RUMAHWEB_HOST`    | Your Rumahweb hosting server | `server.rumahweb.com`                    |
| `RUMAHWEB_USER`    | Your Rumahweb username       | `yourusername`                           |
| `RUMAHWEB_SSH_KEY` | Your private SSH key         | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

### 3. Generate SSH Keys (if needed)

If you don't have SSH keys set up:

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy the public key to Rumahweb
# Add the contents of ~/.ssh/id_rsa.pub to your Rumahweb account's authorized_keys file
```

### 4. Configure Environment Variables on Rumahweb

Create a `.env.production` file in your application directory on Rumahweb:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (if using PostgreSQL)
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Payment Gateway (if using Stripe)
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
```

## How It Works

The GitHub Actions workflow in `.github/workflows/deploy.yml` performs the following steps:

1. **On push to main/production branches**:

   - Runs tests to ensure code quality
   - Builds deployment package
   - Deploys to Rumahweb via SCP
   - Executes remote deployment commands
   - Restarts the application

2. **Deployment Process**:
   - Transfers code via SCP
   - Installs/updates Python dependencies
   - Runs database migrations
   - Collects static files
   - Restarts the application

## Customization

### Branch Configuration

By default, the workflow triggers on pushes to `main`, `master`, and `production` branches. You can modify this in the `on.push.branches` section of the workflow file.

### Environment-specific Deployments

You can create separate workflows for different environments (staging, production) by duplicating the workflow file with different names and configurations.

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**

   - Verify your SSH key is correctly added to GitHub secrets
   - Check that your Rumahweb server allows SSH connections
   - Ensure the SSH key has the correct permissions (not too open)

2. **Deployment Fails**

   - Check the GitHub Actions logs for specific error messages
   - Verify all required secrets are set in GitHub
   - Ensure the target directory on Rumahweb is writable

3. **Application Not Starting**
   - Check the Passenger error logs on Rumahweb
   - Verify the `passenger_wsgi.py` file is correctly configured
   - Ensure all required environment variables are set

### Manual Deployment

If automatic deployment fails, you can manually deploy by:

```bash
# SSH into your Rumahweb account
ssh yourusername@server.rumahweb.com

# Navigate to your application directory
cd /home/yourusername/hybridlms

# Pull the latest code
git pull origin main

# Activate virtual environment
source /path/to/your/venv/bin/activate

# Install/update dependencies
pip install -r requirements-prod.txt

# Run migrations
python manage.py migrate --settings=hybrid_lms.settings_prod

# Collect static files
python manage.py collectstatic --noinput --settings=hybrid_lms.settings_prod

# Restart the application
touch passenger_wsgi.py
```

## Security Considerations

1. **Secrets Management**

   - Never commit sensitive information to the repository
   - Use GitHub Secrets for all sensitive configuration
   - Rotate secrets regularly

2. **Access Control**

   - Limit SSH key access to only necessary operations
   - Use separate deployment keys for different environments
   - Monitor deployment logs for unauthorized access

3. **Environment Isolation**
   - Use separate databases for different environments
   - Isolate staging and production environments
   - Implement proper firewall rules

## Monitoring

The deployment process includes:

- Automated testing before deployment
- Error reporting through GitHub Actions
- Application health checks
- Logging of all deployment activities

For additional monitoring, consider integrating:

- Application performance monitoring (APM) tools
- Error tracking services (Sentry, etc.)
- Uptime monitoring services
