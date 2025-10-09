import os
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# Read from .env file
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Firebase-only Django apps (no database models)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes', 
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',       # Firebase configuration
    'customers',  # Customer management (Firebase)
    'sales',      # Sales management (Firebase)
    'analytics',  # Analytics (Firebase)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crm_project.urls'

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

WSGI_APPLICATION = 'crm_project.wsgi.application'

# Minimal SQLite database ONLY for Django sessions and admin
# All CRM data is stored in Firebase
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / config('DATABASE_NAME', default='db_sessions_only.sqlite3'),
    }
}

# No password validators for development
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (if needed)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Session settings (using database for sessions only)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=86400, cast=int)  # 24 hours

# Firebase settings (loaded from environment)
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='core/serviceAccountKey.json')
FIREBASE_DATABASE_URL = config('FIREBASE_DATABASE_URL', default='')
FIREBASE_PROJECT_ID = config('FIREBASE_PROJECT_ID', default='')
FIREBASE_STORAGE_BUCKET = config('FIREBASE_STORAGE_BUCKET', default='')

# Cache settings (optional, for performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': config('CACHE_TIMEOUT', default=300, cast=int),
    }
}

# Email settings (optional)
if config('EMAIL_HOST_USER', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = config('MAX_UPLOAD_SIZE', default=5242880, cast=int)  # 5MB

# Demo account settings (from env)
DEMO_USER_EMAIL = config('DEMO_USER_EMAIL', default='admin@crm.com')
DEMO_USER_PASSWORD = config('DEMO_USER_PASSWORD', default='admin123')
DEMO_USER_NAME = config('DEMO_USER_NAME', default='Admin User')