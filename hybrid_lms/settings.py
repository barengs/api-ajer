"""
Django settings for hybrid_lms project.
"""
from pathlib import Path
from decouple import config
from datetime import timedelta
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-2024')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_extensions',
    'drf_spectacular',
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
    'social_django',
]

LOCAL_APPS = [
    'accounts',
    'courses',
    'lessons',
    'assignments',
    'forums',
    'payments',
    'notifications',
    'analytics',
    'gamification',
    'live_sessions',
    'role_management',
    'navigation',
    'health',  # Health check app
    'oauth',   # OAuth app
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hybrid_lms.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hybrid_lms.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# For production, use PostgreSQL:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

# Spectacular Settings (API Documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Hybrid LMS API',
    'DESCRIPTION': '''API untuk Sistem Manajemen Pembelajaran Hibrid yang menggabungkan pembelajaran mandiri (self-paced) dan terstruktur (structured learning).
    
    ## Fitur Utama:
    - **Authentication**: Sistem autentikasi JWT dengan role-based access
    - **Course Management**: Pengelolaan kursus untuk self-paced dan structured learning
    - **Learning Experience**: Sistem pembelajaran dengan progress tracking
    - **Payment System**: Integrasi payment gateway untuk e-commerce
    - **Forum & Discussions**: Sistem diskusi dan Q&A
    - **Gamification**: Points, badges, dan leaderboard
    - **Live Sessions**: Integrasi dengan platform video conference
    
    ## Jenis Pengguna:
    - **Student**: Mengikuti kursus dan pembelajaran
    - **Instructor**: Membuat dan mengelola kursus
    - **Admin**: Mengelola platform dan moderasi konten
    
    ## Rate Limiting:
    - Authentication endpoints: 5 requests per minute
    - General API: 100 requests per minute
    - File uploads: 10 requests per minute
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': [],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'displayRequestDuration': True,
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
    },
    'REDOC_UI_SETTINGS': {
        'nativeScrollbars': True,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#1976d2'
                }
            },
            'typography': {
                'fontSize': '14px',
                'lineHeight': '1.5em',
                'code': {
                    'fontSize': '13px'
                },
                'headings': {
                    'fontFamily': 'Roboto, sans-serif'
                }
            }
        }
    },
    'SORT_OPERATIONS': True,
    'SORT_OPERATION_PARAMETERS': True,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'ENUM_NAME_OVERRIDES': {
        'UserRoleEnum': 'accounts.models.User.UserRole',
        'CourseTypeEnum': 'courses.models.Course.CourseType',
        'DifficultyLevelEnum': 'courses.models.Course.DifficultyLevel',
        'CourseStatusEnum': 'courses.models.Course.CourseStatus',
        # Fix enum naming collisions
        'AssignmentStatusEnum': 'assignments.models.Assignment.Status',
        'SubmissionStatusEnum': 'assignments.models.Submission.Status',
        'OrderStatusEnum': 'payments.models.Order.Status',
        'PaymentStatusEnum': 'payments.models.Payment.Status',
        'NotificationStatusEnum': 'notifications.models.Notification.Status',
        'UserRoleAssignmentStatusEnum': 'role_management.models.UserRoleAssignment.Status',
        'UserRoleRequestStatusEnum': 'role_management.models.UserRoleRequest.Status',
    },
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
    ],
    'TAGS': [
        {
            'name': 'Authentication',
            'description': 'Endpoints untuk autentikasi pengguna, registrasi, login, dan manajemen profil'
        },
        {
            'name': 'Courses', 
            'description': 'Pengelolaan kursus, kategori, dan pencarian kursus'
        },
        {
            'name': 'Lessons',
            'description': 'Manajemen konten pembelajaran, video, dan materi'
        },
        {
            'name': 'Assignments',
            'description': 'Sistem tugas dan quiz untuk kursus terstruktur'
        },
        {
            'name': 'Forums',
            'description': 'Sistem diskusi, Q&A, dan interaksi antar pengguna'
        },
        {
            'name': 'Payments',
            'description': 'Sistem pembayaran, shopping cart, dan transaksi'
        },
        {
            'name': 'Notifications',
            'description': 'Sistem notifikasi real-time dan email'
        },
        {
            'name': 'Analytics',
            'description': 'Dashboard analitik dan laporan untuk instruktur dan admin'
        },
        {
            'name': 'Gamification',
            'description': 'Sistem points, badges, dan leaderboard'
        },
        {
            'name': 'Live Sessions',
            'description': 'Integrasi dengan platform video conference untuk kelas live'
        },
        {
            'name': 'Health',
            'description': 'Endpoint untuk monitoring status aplikasi'
        }
    ],
}

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# For production:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST')
# EMAIL_PORT = config('EMAIL_PORT', cast=int)
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Payment Configuration
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Platform Configuration
PLATFORM_COMMISSION_RATE = 0.10  # 10% commission
DEFAULT_CURRENCY = 'USD'

# Health Check Settings
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
}

# Social Auth Configuration
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('GOOGLE_OAUTH2_SECRET', default='')

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.CaseInsensitiveAuth',
    'social_core.backends.google.GoogleOAuth2',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'oauth.pipeline.save_profile',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
