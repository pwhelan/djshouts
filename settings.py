from djangoappengine.settings_base import *

import os

SECRET_KEY = 'glm+85vfc4((7648&sdf3vfc4((7yd0dbrakhvi=r-$b*8h'

INSTALLED_APPS = (
    'djangoappengine',
    'djangotoolbox',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'filetransfers',
    'deejaypages',
    'facebook',
    'facebook_connect'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
)

LOGIN_REDIRECT_URL = '/shows/'

ADMIN_MEDIA_PREFIX = '/media/admin/'
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media')
TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)

ROOT_URLCONF = 'urls'

AUTHENTICATION_BACKENDS = ('facebook.backend.FacebookBackend', 'django.contrib.auth.backends.ModelBackend')
AUTH_PROFILE_MODULE = 'facebook.FacebookProfile'
FACEBOOK_APP_ID = '119199201567960' # os.environ['FACEBOOK_APP_ID']
FACEBOOK_APP_SECRET = '272e00b0a45c5876094a51c300b2cfd1' # os.environ['FACEBOOK_APP_SECRET']
FACEBOOK_SCOPE = 'email,publish_stream'
FACEBOOK_FORCE_SIGNUP = True

