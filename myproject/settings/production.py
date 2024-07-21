from .base import *
import os
import dj_database_url
from environ import Env

# Initialize environment variables
env = Env(
    DEBUG=(bool, False)
)

# Read .env file
env.read_env(os.path.join(BASE_DIR, '.env'))

DEBUG = env.bool('DEBUG', default=False)

SECRET_KEY = env('SECRET_KEY')

# Directly set the ALLOWED_HOSTS to include your domain
ALLOWED_HOSTS = ['chinese-django.onrender.com', 'localhost', '127.0.0.1', 'www.chineselog.com', 'chineselog.com']

# Database configuration
DATABASES = {
    'default': dj_database_url.config(default=env('DATABASE_URL'))
}

GOOGLE_API_KEY = env('GOOGLE_API_KEY')

# Security settings
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Superuser credentials from environment variables
SUPERUSER_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME')
SUPERUSER_EMAIL = os.getenv('DJANGO_SUPERUSER_EMAIL')
SUPERUSER_PASSWORD = os.getenv('DJANGO_SUPERUSER_PASSWORD')