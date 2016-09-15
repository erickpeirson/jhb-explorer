"""
Django settings for jhb project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
from urlparse import urlparse
import socket
import dj_database_url

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

SECRET_KEY = os.environ.get('SECRET_KEY', '(z!a=e2w+6l4lmh#&5=!0gfj&l8=+0m6syech$$7*$v1bp^i=&')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = eval(os.environ.get('DEBUG', 'False'))
DEBUG=True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'haystack',
    'django_extensions',
    'rest_framework',
    'explorer',
)

MIDDLEWARE_CLASSES = (
    'sslify.middleware.SSLifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'explorer.middleware.StartEndYearMiddleWare',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'explorer.context_processors.google_analytics_config',
                'explorer.context_processors.timeline_dates',
            ],
        },
    },
]

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}

ROOT_URLCONF = 'jhb.urls'


WSGI_APPLICATION = 'jhb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'jhbexplorer',
        'USER': 'jhbexplorer',
        'PASSWORD': 'jhbexplorer',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# import dj_database_url
# DATABASES['default'] =  dj_database_url.config()


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

MEDIA_URL = '/media/'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, '..', 'explorer', 'static'),
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'jhb_cachetable',
    }
}

es = urlparse(os.environ.get('SEARCHBOX_URL') or 'http://127.0.0.1:9200/')
port = es.port or 80

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'explorer.elasticsearch_backends.JHBElasticsearch2SearchEngine',
        'URL': es.scheme + '://' + es.hostname + ':' + str(port),
        'INDEX_NAME': 'jhb',
    },
}

if es.username:
    HAYSTACK_CONNECTIONS['default']['KWARGS'] = {"http_auth": es.username + ':' + es.password}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

VOGONWEB = 'http://www.vogonweb.net'


SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SSLIFY_DISABLE = True       # The development server will choke on SSL.

HAYSTACK_SEARCH_RESULTS_PER_PAGE = 20


GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', None)


MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJpY2twZWlyc29uIiwiYSI6ImNpdDJ4bmcxYTB0azEyenFwZ25sdXBzbTQifQ.CfYrsRYjuRRUJSJo8PmnBA'
