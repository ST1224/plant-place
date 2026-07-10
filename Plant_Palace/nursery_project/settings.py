"""
Django settings for Nursery Management System (Plant Palace).
Production-ready configuration.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY
# ---------------------------------------------------------------------------
# Load secret key from environment; fall back to a safe development value.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'change-me-in-production-use-env-variable-plant-palace-nursery-2024'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# ---------------------------------------------------------------------------
# APPLICATION DEFINITION
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop.apps.ShopConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nursery_project.urls'

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
                'shop.context_processors.cart_count',  # Global cart count
                'shop.context_processors.dashboard_counts',  # Admin sidebar badges
            ],
        },
    },
]

WSGI_APPLICATION = 'nursery_project.wsgi.application'

# ---------------------------------------------------------------------------
# DATABASE — SQLite for development (swap ENGINE/NAME for production DB)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
# USE_L10N removed — deprecated in Django 4+ (always True by default)
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'shop' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # Used by collectstatic in production

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# EMAIL — Use console backend in development; configure SMTP in production.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# For production, swap to:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# ---------------------------------------------------------------------------
# AUTH REDIRECTS
# ---------------------------------------------------------------------------
LOGIN_URL = '/login/'  # renders login_page view
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ---------------------------------------------------------------------------
# DEFAULT AUTO FIELD
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# PAYMENT SETTINGS (Simulation — replace with real gateway credentials)
# ---------------------------------------------------------------------------
PAYMENT_MERCHANT_ID = os.environ.get('PAYMENT_MERCHANT_ID', 'DEMO_MERCHANT_ID')
PAYMENT_MERCHANT_KEY = os.environ.get('PAYMENT_MERCHANT_KEY', 'DEMO_MERCHANT_KEY')
PAYMENT_CALLBACK_URL = os.environ.get('PAYMENT_CALLBACK_URL', 'http://127.0.0.1:8000/payment/callback/')

# ---------------------------------------------------------------------------
# MESSAGES TAGS — Map Django message levels to Bootstrap alert classes
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as msg_constants
MESSAGE_TAGS = {
    msg_constants.DEBUG: 'secondary',
    msg_constants.INFO: 'info',
    msg_constants.SUCCESS: 'success',
    msg_constants.WARNING: 'warning',
    msg_constants.ERROR: 'danger',
}
