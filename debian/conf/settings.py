# Django settings for ddrpublic.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# ----------------------------------------------------------------------

import ConfigParser
import logging
import os

class NoConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

CONFIG_FILE = '/etc/ddr/ddr.cfg'
if not os.path.exists(CONFIG_FILE):
    raise NoConfigError('No config file!')
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)

LOG_FILE='/var/log/ddr/public.log'
LOG_LEVEL=DEBUG

SECRET_KEY='ivb=&yqv^#%_i5v&c*qa@aaa#=z-(t$i=k*geugb_!2ky&j0ca'

LANGUAGE_CODE='en-us'
TIME_ZONE='America/Los_Angeles'

# Filesystem path and URL for static media (mostly used for interfaces).
STATIC_ROOT='/var/www/static'
STATIC_URL='/static/'

# Filesystem path and URL for media to be manipulated by ddrlocal
# (collection repositories, thumbnail cache, etc).
MEDIA_ROOT='/var/www/media'
MEDIA_URL='http://ddr.densho.org/media/'

ACCESS_FILE_APPEND='-a'
ACCESS_FILE_EXTENSION='.jpg'
ACCESS_FILE_GEOMETRY='1024x1024>'
ACCESS_FILE_OPTIONS=''
THUMBNAIL_GEOMETRY='512x512>'
THUMBNAIL_OPTIONS=''

# Directory in root of USB HDD that marks it as a DDR disk
# /media/USBHDDNAME/ddr
DDR_USBHDD_BASE_DIR = 'ddr'

MEDIA_BASE = os.path.join(MEDIA_ROOT, 'base')

ENTITY_FILE_ROLES = (
    ('master','master'),
    ('mezzanine','mezzanine'),
    ('access','access'),
)

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S:%f'
# Django uses a slightly different datetime format
DATETIME_FORMAT_FORM = '%Y-%m-%d %H:%M:%S'

PRETTY_DATE_FORMAT = '%d %B %Y'
PRETTY_TIME_FORMAT = '%I:%M %p'
PRETTY_DATETIME_FORMAT = '%d %B %Y, %I:%M %p'

# ----------------------------------------------------------------------

ADMINS = (
    ('geoffrey jost', 'geoffrey.jost@densho.org'),
    ('Geoff Froh', 'geoff.froh@densho.org'),
)
MANAGERS = ADMINS

SITE_ID = 1

INSTALLED_APPS = (
    #'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.admin',
    #
    'bootstrap_pagination',
    'sorl.thumbnail',
    #
    'ddrpublic',
    'ui',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/var/lib/ddr/ddrpublic.db',
    }
}

REDIS_HOST = '127.0.0.1'
REDIS_PORT = '6379'
REDIS_DB_CACHE = 0
REDIS_DB_SORL = 3

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "%s:%s:%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB_CACHE),
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

# ElasticSearch
ELASTICSEARCH_HOST = 'localhost'
ELASTICSEARCH_PORT = '9200'
ELASTICSEARCH_HOST_PORT = ':'.join([ELASTICSEARCH_HOST, ELASTICSEARCH_PORT])
ELASTICSEARCH_MAX_SIZE = 1000000

RESULTS_PER_PAGE = 25

DOCUMENT_INDEX = 'documents'
METADATA_INDEX = 'meta'

# sorl-thumbnail
THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_DEBUG = False
#THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore'
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_REDIS_PASSWORD = ''
THUMBNAIL_REDIS_HOST = REDIS_HOST
THUMBNAIL_REDIS_PORT = int(REDIS_PORT)
THUMBNAIL_REDIS_DB = REDIS_DB_SORL
THUMBNAIL_ENGINE = 'sorl.thumbnail.engines.convert_engine.Engine'
THUMBNAIL_CONVERT = 'convert'
THUMBNAIL_IDENTIFY = 'identify'
THUMBNAIL_CACHE_TIMEOUT = 60*60*24*365*10  # 10 years
THUMBNAIL_DUMMY = False
THUMBNAIL_URL_TIMEOUT = 60  # 1min

# File thumbnail URL generator function
# sorl.thumbnail will download original files from this source and generate thumbnails locally.
# This may point to a local or remote machine.
# Function for generating access file URLs; source media may be on local or remote system.

# Local VM
def UI_THUMB_URL(ddrfile):
    """Example:
    http://192.168.56.101/media/base/ddr-testing-123/files/ddr-testing-123-1/files/ddr-testing-123-1-master-a1b2c3d4e5-a.jpg
    """
    return 'http://192.168.56.101/media/base/%s/files/%s/files/%s' % (
        ddrfile.collection_id, ddrfile.entity_id, ddrfile.access_rel)

# colo
def UI_THUMB_URL(ddrfile):
    """Example:
    /media/ddr-testing-123/ddr-testing-123-1-master-a1b2c3d4e5-a.jpg
    """
    return '%s%s/%s' % (MEDIA_URL, ddrfile.collection_id, ddrfile.access_rel)

# # Amazon S3
# def UI_THUMB_URL(ddrfile):
#     """Example:
#     https://densho-ddr.s3.amazonaws.com/ddr-testing-123/ddr-testing-123-1-master-a1b2c3d4e5-a.jpg
#     """
#     bucket = 'densho-ddr'
#     folder = ddrfile.collection_id
#     object_key = ddrfile.access_rel
#     return 'https://%s.s3.amazonaws.com/%s/%s' % (bucket, folder, object_key)


# Local VM, colo
def UI_DOWNLOAD_URL( ddrfile ):
    """Construct download URL if this is a mezzanine (no downloads for masters)
    
    ex: http://ddr.densho.org/media/ddr-densho-10/ddr-densho-10-2-mezzanine-768fb04ca7.tif
    
    TODO include path_rel in the index so we don't have to do all this
    """
    if ddrfile.role == u'mezzanine':
        extension = os.path.splitext(ddrfile.basename_orig)[1]
        filename = ddrfile.id + extension
        path_rel = os.path.join(ddrfile.collection_id, filename)
        url = MEDIA_URL + path_rel
        return url
    return None


#SESSION_ENGINE = 'redis_sessions.session'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

TEMPLATE_DIRS = (
    '/usr/local/src/ddr-public/ddrpublic/ui/templates',
)

STATICFILES_DIRS = (
    #'/opt/ddr-local/ddrpublic/ddrpublic/static',
    #'/usr/local/src/ddr-local/ddrpublic/storage/static',
    '/usr/local/src/ddr-local/ddrpublic/ui/static',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)-8s [%(module)s.%(funcName)s]  %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)-8s %(message)s'
        },
    },
    'filters': {
        # only log when settings.DEBUG == False
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILE,
            'when': 'D',
            'backupCount': 14,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'level': 'ERROR',
            'propagate': True,
            'handlers': ['mail_admins'],
        },
    },
    # This is the only way I found to write log entries from the whole DDR stack.
    'root': {
        'level': 'DEBUG',
        'handlers': ['file'],
    },
}

USE_TZ = True
USE_I18N = True
USE_L10N = True

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    #'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    #'django.contrib.messages.context_processors.messages',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ui.urls'

WSGI_APPLICATION = 'ddrpublic.wsgi.application'
