import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


env_vars = [
    ('IP_ADDRESS', 'IP_ADDRESS'),
    ('JWT_SECRET_KEY', 'JWT_SECRET_KEY'),
    ('PONG_OAUTH_UID', 'PONG_OAUTH_UID'),
    ('PONG_OAUTH_42_SECRET', 'PONG_OAUTH_42_SECRET'),
    ('AUTH_SERVICE_SECRET_KEY', 'SECRET_KEY'),
    ('EMAIL_PASSWORD', 'EMAIL_PASSWORD'),
]

for env_var, var in env_vars:
    value = os.getenv(env_var)
    if value is None:
        raise ImproperlyConfigured(f'{env_var} environment variable is required')
    globals()[var] = value

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'auth_app',
	'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'auth_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

ASGI_APPLICATION = 'auth_service.asgi.application'

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', IP_ADDRESS]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = '2fa.tester2@gmail.com'
EMAIL_HOST_PASSWORD = EMAIL_PASSWORD
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

CORS_ALLOWED_ORIGINS = [
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8003"
]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


#HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True

CSRF_COOKIE_NAME = 'csrf_token_auth_service'
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = True
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    f"https://{IP_ADDRESS}:8443",
    f"https://{IP_ADDRESS}:8003"
]

CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'auth_service.utils.json_formatter.JsonFormatter',
        },
        'console': {
            '()': 'auth_service.utils.console_formatter.ConsoleFormatter',
            'format': '%(message)s',
        },
    },
    'handlers': {
        'logstash': {
            'level': 'DEBUG',
            'class': 'auth_service.utils.ssl_socket_handler.SSLSocketHandler',
            'host': 'logstash',
            'port': 5044,
            'ssl_certfile': '/etc/ssl/auth-service.crt',
            'ssl_keyfile': '/etc/ssl/auth-service.key',
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'auth-service': {
            'handlers': ['logstash', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
