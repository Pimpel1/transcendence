import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env_vars = [
    ('IP_ADDRESS', 'IP_ADDRESS'),
    ('MATCHMAKER_SERVICE_SECRET_KEY', 'SECRET_KEY'),
    ('MATCHMAKER_SERVICE_API_KEY', 'MATCHMAKER_SERVICE_API_KEY'),
]

for env_var, var in env_vars:
    value = os.getenv(env_var)
    if value is None:
        raise ImproperlyConfigured(f'{env_var} environment variable is required')
    globals()[var] = value

DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', IP_ADDRESS]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'channels',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'matchmaker_app',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'matchmaker_app.urls'

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

ASGI_APPLICATION = 'matchmaker_service.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = ['*']

CORS_ALLOWED_ORIGINS = [
    "https://localhost:8443",
    "https://localhost:8000",
    "https://localhost:8001",
    "https://localhost:8003",
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8000",
    f"https://{IP_ADDRESS}:8001",
    f"https://{IP_ADDRESS}:8003",
]

CSRF_TRUSTED_ORIGINS = [
    'https://localhost:8443',
    'https://game-service:8001',
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8003",
    f"https://{IP_ADDRESS}:8001",
]

#HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_NAME = 'csrf_token_matchmaker_service'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = False

CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'matchmaker_service.utils.json_formatter.JsonFormatter',
        },
        'console': {
            '()': 'matchmaker_service.utils.console_formatter.ConsoleFormatter',
            'format': '%(message)s',
        },
    },
    'handlers': {
        'logstash': {
            'level': 'DEBUG',
            'class': 'matchmaker_service.utils.ssl_socket_handler.SSLSocketHandler',
            'host': 'logstash',
            'port': 5044,
            'ssl_certfile': '/etc/ssl/matchmaker-service.crt',
            'ssl_keyfile': '/etc/ssl/matchmaker-service.key',
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'matchmaker-service': {
            'handlers': ['logstash', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}