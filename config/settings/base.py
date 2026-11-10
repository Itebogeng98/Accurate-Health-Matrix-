from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = [host.strip() for host in config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',') if host.strip()]
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','rest_framework.authtoken',
    'apps.authentication.apps.AuthenticationConfig', 'apps.core.apps.CoreConfig',
    'apps.core.legacy.predictions.apps.PredictionsConfig',
    'apps.core.legacy.wellness.apps.WellnessConfig',
]
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','apps.authentication.activity.UserActivityMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR / 'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'), 
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('PORT'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
AUTH_USER_MODEL = 'accounts.CustomUser'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Retain the existing migration history and database identity.
MIGRATION_MODULES = {'accounts': 'apps.authentication.migrations',
                     'predictions': 'apps.core.legacy.predictions.migrations',
                     'wellness': 'apps.core.legacy.wellness.migrations'}

ASGI_APPLICATION = 'config.asgi.application'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# SendGrid API email. Credentials stay in the environment, never in source control.
def clean_env_value(name, default=""):
    return config(name, default=default).strip().strip('"').strip("'")

SENDGRID_API_KEY = clean_env_value('SENDGRID_API_KEY') or clean_env_value('EMAIL_HOST_PASSWORD')
EMAIL_BACKEND = clean_env_value('EMAIL_BACKEND')
if EMAIL_BACKEND in ('', 'summit.email_backend.SendGridAPIBackend') or (
        SENDGRID_API_KEY and EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'):
    EMAIL_BACKEND = ('apps.core.email_backend.SendGridAPIBackend' if SENDGRID_API_KEY
                     else 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = clean_env_value('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=15, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = clean_env_value('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = clean_env_value('EMAIL_HOST_PASSWORD') or SENDGRID_API_KEY
DEFAULT_FROM_EMAIL = clean_env_value('DEFAULT_FROM_EMAIL', 'noreply@example.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
