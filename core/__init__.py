import os
import sys

from django.apps import apps
from django.apps.registry import Apps

_settings = sys.modules['django.conf'].settings

if 'core' in getattr(_settings, 'INSTALLED_APPS'):
    try:
        setattr(_settings, 'EMAIL_USE_TLS', True)
        setattr(_settings, 'DEFAULT_FROM_EMAIL', os.getenv('DEFAULT_FROM_EMAIL'))
        setattr(_settings, 'EMAIL_HOST', os.getenv('EMAIL_HOST'))
        setattr(_settings, 'EMAIL_HOST_USER', os.getenv('EMAIL_HOST_USER'))
        setattr(_settings, 'EMAIL_HOST_PASSWORD', os.getenv('EMAIL_HOST_PASSWORD'))
        setattr(_settings, 'EMAIL_PORT', os.getenv('EMAIL_PORT'))
    except:
        setattr(_settings, 'EMAIL_USE_TLS', False)
        setattr(_settings, 'DEFAULT_FROM_EMAIL', '')
        setattr(_settings, 'EMAIL_HOST', '')
        setattr(_settings, 'EMAIL_HOST_USER', '')
        setattr(_settings, 'EMAIL_HOST_PASSWORD', '')
        setattr(_settings, 'EMAIL_PORT', '')
    setattr(_settings, 'LOGIN_REDIRECT_URL', '/core/')
    setattr(_settings, 'LOGIN_URL', '/core/login/')
    setattr(_settings, 'LOGOUT_REDIRECT_URL', '/core/login/')
