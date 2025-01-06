'''
Created on 7 mai 2021

@author: S047432
'''
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

INSTALLED_APPS = [
    'django_dramatiq',
    'django.contrib.admin',
    'django.contrib.auth',
    'mozilla_django_oidc',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'django_apscheduler',
    'snapshotServer.app.SnapshotServerConfig',
    'variableServer.app.VariableserverConfig',
    'commonsServer.apps.CommonsserverConfig',
    'elementInfoServer.app.ElementinfoserverConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# both settings are needed to allow viewing test results from seleniumRobot HTML file. Else session and CSRF cookies are not set
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None
# CSRF_COOKIE_SECURE = True  # may be needed when site is exposed in HTTPS


ROOT_URLCONF = 'seleniumRobotServer.urls'

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

WSGI_APPLICATION = 'seleniumRobotServer.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Dramatiq settings
DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": 'redis://<server>:6379/0',
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
        #"django_dramatiq.middleware.AdminMiddleware",
    ]
}

DRAMATIQ_RESULT_BACKEND = {
    "BACKEND": "dramatiq.results.backends.redis.RedisBackend",
    "BACKEND_OPTIONS": {
        "url": "redis://localhost:6379",
    },
    "MIDDLEWARE_OPTIONS": {
        "result_ttl": 1000 * 60 * 10
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

os.makedirs(os.path.join(BASE_DIR, 'log'), exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': { 
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'development_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + '/log/django_dev.log',
            'maxBytes': 5000000,
            'backupCount': 3,
            'formatter': 'verbose'
        },
        'production_logfile': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + '/log/django_production.log',
            'maxBytes': 5000000,
            'backupCount': 3,
            'formatter': 'simple'
        },
        'variableReservation_logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + '/log/variable_reservation.log',
            'formatter': 'simple',
            'maxBytes': 5000000,
            'backupCount': 3
        },
        'dba_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_false','require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + '/log/django_dba.log', 
            'formatter': 'simple',
            'maxBytes': 5000000,
            'backupCount': 3,
        },
    },
    'loggers': {
        'variableServer.views.api_view': {
            'handlers': ['console', 'variableReservation_logfile'],
            'level': 'INFO',
         },
        'snapshotServer': {
            'handlers': ['console','development_logfile','production_logfile'],
            'level': 'DEBUG',
         },
        'django': {
            'handlers': ['console','development_logfile','production_logfile'],
        },
        'py.warnings': {
            'handlers': ['console','development_logfile'],
        },
        'django_auth_ldap': {
            'level': 'DEBUG',
            'handlers': ['console', 'development_logfile'],
        },
        'mozilla_django_oidc': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
    }
}

DELETE_STEP_REFERENCE_AFTER_DAYS = 30       # number of days after which old references will be deleted if they have not been updated. 30 days by default
COMPRESS_IMAGE_FOR_SUCCESS_AFTER_DAYS = 5   # number of days after which images of successful test (except step references and snapshot for comparison) will be compressed at 85%
COMPRESS_IMAGE_FOR_FAILURE_AFTER_DAYS = 10  # number of days after which images of failed test (except step references and snapshot for comparison) will be compressed at 85%
DELETE_HTML_FOR_SUCCESS_AFTER_DAYS = 5      # number of days after which HTML of successful test will be replaced by empty code
DELETE_HTML_FOR_FAILURE_AFTER_DAYS = 10     # number of days after which HTML of failed test will be replaced by empty code
DELETE_VIDEO_FOR_SUCCESS_AFTER_DAYS = 15    # number of days after which HTML of successful test will be deleted
CLEANING_CRON = "0 3 * * *"                 # clean every day at 3 a.m