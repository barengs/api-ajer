"""
WSGI config for Hybrid LMS deployment on Rumahweb/cPanel hosting using Passenger.
This file is used by Passenger to serve the Django application.
"""

import os
import sys
import django.core.handlers.wsgi
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hybrid_lms.settings_prod')

# Set script name for the PATH_INFO fix below
SCRIPT_NAME = os.getcwd()

class PassengerPathInfoFix(object):
    """
    Sets PATH_INFO from REQUEST_URI because Passenger doesn't provide it.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        from urllib.parse import unquote
        environ['SCRIPT_NAME'] = SCRIPT_NAME
        request_uri = unquote(environ['REQUEST_URI'])
        script_name = unquote(environ.get('SCRIPT_NAME', ''))
        offset = request_uri.startswith(script_name) and len(environ['SCRIPT_NAME']) or 0
        environ['PATH_INFO'] = request_uri[offset:].split('?', 1)[0]
        return self.app(environ, start_response)

# Create the WSGI application
application = get_wsgi_application()
application = PassengerPathInfoFix(application)