"""Isolated regression database; never connects to the configured MySQL database."""
from .settings.development import *  # noqa: F401,F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
