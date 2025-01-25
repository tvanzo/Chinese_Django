from .base import *

DEBUG = True

SECRET_KEY = env('SECRET_KEY', default='your-local-secret-key')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Google API Key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Stripe API Keys
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', default='NOT_SET')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', default='NOT_SET')

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
