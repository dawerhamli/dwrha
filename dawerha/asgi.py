"""
ASGI config for dawerha project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dawerha.settings')
application = get_asgi_application()
