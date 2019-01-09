"""
Django settings for seleniumRobotServer project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/

/!\ THIS FILE aims at being processed by a tool which will replace all variables ('${var}')
    by their values
"""



import os
from django_auth_ldap.config import LDAPSearch, LDAPGroupQuery,\
    ActiveDirectoryGroupType
import ldap

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '${django.secret.key}'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'snapshotServer.app.SnapshotServerConfig',
    'variableServer.app.VariableserverConfig',
    'commonsServer.apps.CommonsserverConfig',
    'django_nose',
]

#TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--with-coverage',
    '--with-xunit',
    '--cover-package=snapshotServer',
    '--cover-branches',
    '--cover-inclusive',
    '--cover-erase',
    '--cover-html',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

AUTHENTICATION_BACKENDS = (
    "${ldap.backends}",
    'django.contrib.auth.backends.ModelBackend',
    )

WSGI_APPLICATION = 'seleniumRobotServer.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

if ("${database.host}"): 
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': '${database.name}',
            'USER': '${database.user}',
            'PASSWORD': '${database.password}',
            'HOST': '${database.host}',
            'PORT': '${database.port}',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': "${database.name}",
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        } 
    }


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


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        #'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
        'rest_framework.permissions.AllowAny'
    ]
}

os.makedirs(os.path.join(BASE_DIR, 'log'), exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
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
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/log/django_dev.log',
            'formatter': 'verbose'
        },
        'production_logfile': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/log/django_production.log',
            'formatter': 'simple'
        },
        'dba_logfile': {
            'level': 'DEBUG',
            'filters': ['require_debug_false','require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/log/django_dba.log', 
            'formatter': 'simple'
        },
    },
    'loggers': {
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
    }
}

# -------- Application specific flags ------------
# whether we restrict the view/change/delete/add to the user, in admin view to only applications he has rights for (issue #28)
RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN = False

# first LDAP server configuration
AUTH_LDAP_1_SERVER_URI = "${ldap.url}"
AUTH_LDAP_1_BIND_DN = '${ldap.user}'
AUTH_LDAP_1_BIND_PASSWORD = '${ldap.password}'
AUTH_LDAP_1_USER_SEARCH = LDAPSearch("${ldap.base}", ldap.SCOPE_SUBTREE, "(${ldap.object.class}=%(user)s)")
AUTH_LDAP_1_GROUP_SEARCH = LDAPSearch("${ldap.base}", ldap.SCOPE_SUBTREE, "(objectClass=group)")
AUTH_LDAP_1_GROUP_TYPE = ActiveDirectoryGroupType()
AUTH_LDAP_1_USER_FLAGS_BY_GROUP = {
    "is_active": (LDAPGroupQuery("${ldap.group.admin}") |
                  LDAPGroupQuery("${ldap.group.edit}")),
    "is_staff": "${ldap.group.edit}",
    "is_superuser": "${ldap.group.admin}"
}

# second LDAP server configuration (uncomment "seleniumRobotServer.ldapbackends.LDAPBackend2" in AUTHENTICATION_BACKENDS to use it)
AUTH_LDAP_2_SERVER_URI = "${ldap.2.url}"
AUTH_LDAP_2_BIND_DN = '${ldap.2.user}'
AUTH_LDAP_2_BIND_PASSWORD = '${ldap.2.password}'
AUTH_LDAP_2_USER_SEARCH = LDAPSearch("${ldap.2.base}", ldap.SCOPE_SUBTREE, "(${ldap.2.object.class}=%(user)s)")
AUTH_LDAP_2_GROUP_SEARCH = LDAPSearch("${ldap.2.base}", ldap.SCOPE_SUBTREE, "(objectClass=group)")
AUTH_LDAP_2_GROUP_TYPE = ActiveDirectoryGroupType()
AUTH_LDAP_2_USER_FLAGS_BY_GROUP = {
    "is_active": (LDAPGroupQuery("${ldap.2.group.admin}") |
                  LDAPGroupQuery("${ldap.2.group.edit}")),
    "is_staff": "${ldap.2.group.edit}",
    "is_superuser": "${ldap.2.group.admin}"
}
                                   
# third LDAP server configuration (uncomment "seleniumRobotServer.ldapbackends.LDAPBackend3" in AUTHENTICATION_BACKENDS to use it)
AUTH_LDAP_3_SERVER_URI = "${ldap.3.url}"
AUTH_LDAP_3_BIND_DN = '${ldap.3.user}'
AUTH_LDAP_3_BIND_PASSWORD = '${ldap.3.password}'
AUTH_LDAP_3_USER_SEARCH = LDAPSearch("${ldap.3.base}", ldap.SCOPE_SUBTREE, "(${ldap.3.object.class}=%(user)s)")
AUTH_LDAP_3_GROUP_SEARCH = LDAPSearch("${ldap.3.base}", ldap.SCOPE_SUBTREE, "(objectClass=group)")
AUTH_LDAP_3_GROUP_TYPE = ActiveDirectoryGroupType()
AUTH_LDAP_3_USER_FLAGS_BY_GROUP = {
    "is_active": (LDAPGroupQuery("${ldap.3.group.admin}") |
                  LDAPGroupQuery("${ldap.3.group.edit}")),
    "is_staff": "${ldap.3.group.edit}",
    "is_superuser": "${ldap.3.group.admin}"
}