import os
import sys

from django.apps import apps
from django.apps.registry import Apps

_settings = sys.modules['django.conf'].settings

if 'core' in getattr(_settings, 'INSTALLED_APPS'):
    setattr(_settings, 'LOGIN_REDIRECT_URL', '/core/')
    setattr(_settings, 'LOGIN_URL', '/core/login/')
    setattr(_settings, 'LOGOUT_REDIRECT_URL', '/core/login/')
        
    
