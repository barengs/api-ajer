"""
ASGI config for hybrid_lms project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings')

application = get_asgi_application()