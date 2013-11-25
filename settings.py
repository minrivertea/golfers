# Django settings for golfers project.


import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])


DEBUG = True
TEMPLATE_DEBUG = DEBUG
SITE_URL = 'http://www.pro-advanced.com'

ADMINS = (
    ('Chris West', 'chris@minrivertea.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

TIME_ZONE = 'Europe/London'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    #'django.core.context_processors.debug',
    'django.core.context_processors.request',
    'django.core.context_processors.i18n',
    'shop.context_processors.get_basket',
    'shop.context_processors.get_basket_quantity',
    'shop.context_processors.common',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

AUTHENTICATION_BACKENDS = (
    "emailauth.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
)


ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, "templates/")
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
#    'django.contrib.flatpages',
    'django.contrib.sitemaps',
    'shop',
    'sorl.thumbnail',
    'paypal.standard.ipn',
    'tinymce',
    'blog',
    'modeltranslation',
    'rosetta',
    'captcha',
)

# DJANGO-CAPTCHA
# -----------------------------------------------
#CAPTCHA_FONT_SIZE = 35
#CAPTCHA_LETTER_ROTATION = None

# Random app information for different things
ACCOUNT_ACTIVATION_DAYS = 7
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_PORT = ''
SERVER_EMAIL = 'sales@pro-advanced.com'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

PAYPAL_IDENTITY_TOKEN = ""
PAYPAL_RECEIVER_EMAIL = ""

# language stuff
USE_I18N = True
USE_L10N = False
gettext = lambda s: s
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', gettext('English')),
    ('fr', gettext('French')),
    ('it', gettext('Italian')),
)

LOCALE_PATHS = (
    os.path.join(PROJECT_PATH, "locale")
)
MODELTRANSLATION_TRANSLATION_REGISTRY = "translation"



GA_IS_ON = True

SITE_EMAIL = 'sales@pro-advanced.com'
SHIPPING_PRICE_LOW = 29.99
SHIPPING_PRICE_HIGH = 57.00

PROJECT_NAME = 'Pro-Advanced'

TINYMCE_JS_URL = "js/tiny_mce/tiny_mce.js"
TINYMCE_JS_ROOT = "js/tiny_mce"
TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,paste,searchreplace",
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
}

LOG_FILENAME = "/var/log/django/golfers.log"

try:
    from local_settings import *
except ImportError:
    pass
               
