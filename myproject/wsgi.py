# myproject/wsgi.py
import os
import logging
from django.core.wsgi import get_wsgi_application

# Initialize the logger
logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')

application = get_wsgi_application()

# Log Gunicorn settings at startup
logger.info(f"Gunicorn command: {os.environ.get('GUNICORN_CMD_ARGS', 'Not set')}")