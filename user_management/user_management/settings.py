import os
import sys
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

env_vars = [
    ('IP_ADDRESS', 'IP_ADDRESS'),
    ('JWT_SECRET_KEY', 'JWT_SECRET_KEY'),
    ('USER_MANAGEMENT_SECRET_KEY', 'SECRET_KEY'),
    ('MATCHMAKER_SERVICE_API_KEY', 'MATCHMAKER_SERVICE_API_KEY'),
]

for env_var, var in env_vars:
    value = os.getenv(env_var)
    if value is None:
        raise ImproperlyConfigured(f'{env_var} environment variable is required')
    globals()[var] = value

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', IP_ADDRESS]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'user_app',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'user_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'user_management.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'PORT': os.environ.get('DB_PORT')
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = ['*']

AUTH_USER_MODEL = 'user_app.User'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

CORS_ALLOWED_ORIGINS = [
    "https://localhost:8443",
    "https://localhost:8001",
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8001",
]

#HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_NAME = 'csrf_token_user_management'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8443',
    'https://localhost:8001',
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8001",
]


CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'user_management.utils.json_formatter.JsonFormatter',
        },
        'console': {
            '()': 'user_management.utils.console_formatter.ConsoleFormatter',
            'format': '%(message)s',
        },
    },
    'handlers': {
        'logstash': {
            'level': 'DEBUG',
            'class': 'user_management.utils.ssl_socket_handler.SSLSocketHandler',
            'host': 'logstash',
            'port': 5044,
            'ssl_certfile': '/etc/ssl/user-management.crt',
            'ssl_keyfile': '/etc/ssl/user-management.key',
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'user-management': {
            'handlers': ['logstash', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
