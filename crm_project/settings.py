import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Pure Firebase - NO Django models at all
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # Minimal for Django to work
    'django.contrib.sessions',      # For session management
    'django.contrib.messages',      # For flash messages
    'django.contrib.staticfiles',   # For CSS/JS files
    'customers',                    # Firebase schemas only
    'sales',                        # Firebase schemas only
    'analytics',                    # Firebase queries only
    'core',                         # Firebase configuration
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
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
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crm_project.wsgi.application'

# No database needed for business data - only for Django sessions
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database (no file created)
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# No login URLs needed - Firebase handles auth
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Firebase settings
FIREBASE_CONFIG = {
    'use_local_mode': True,  # Set to False when you have Firebase credentials
    'collections': {
        'users': 'users',               # Firebase Auth users
        'customers': 'customers',
        'deals': 'deals', 
        'employees': 'employees',
        'tasks': 'tasks',
        'interactions': 'interactions',
        'sales_activities': 'sales_activities',
        'pipeline_history': 'pipeline_history'
    }
}