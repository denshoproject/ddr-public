# Django settings for ddrpublic.

ENCYC_BASE = 'http://encyclopedia.densho.org'

# ----------------------------------------------------------------------

import ConfigParser
import logging
import os

class NoConfigError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

CONFIG_FILES = [
    '/etc/ddr/ddrpublic.cfg',
    '/etc/ddr/ddrpublic-local.cfg'
]
config = ConfigParser.ConfigParser()
configs_read = config.read(CONFIG_FILES)
if not configs_read:
    raise NoConfigError('No config file!')

with open('/etc/ddr/ddrpublic-secret-key.txt') as f:
    SECRET_KEY = f.read().strip()

LANGUAGE_CODE='en-us'
TIME_ZONE='America/Los_Angeles'

DEBUG = config.get('debug', 'debug')
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = config.get('debug', 'thumbnail')

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    host.strip()
    for host in config.get('public', 'allowed_hosts').split(',')
]
# partner-branded domains
PARTNER_DOMAINS = {
    'hmwf': ['hmwf.ddr.densho.org', 'hmwf.ddr.local',],
    'janm': ['janm.ddr.densho.org', 'janm.ddr.local',],
    'one': ['one.ddr.densho.org', 'one.ddr.local',],
    'testing': ['testing.ddr.densho.org', 'testing.ddr.local',],
}
for value in PARTNER_DOMAINS.values():
    for domain in value:
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)

# Elasticsearch
DOCSTORE_HOSTS = [{
    'host':config.get('public', 'docstore_host').split(':')[0],
    'port':config.get('public', 'docstore_host').split(':')[1],
}]
DOCSTORE_INDEX = config.get('public', 'docstore_index')
NAMESDB_DOCSTORE_HOSTS = [{
    'host':config.get('public', 'namesdb_host').split(':')[0],
    'port':config.get('public', 'namesdb_host').split(':')[1],
}]
NAMESDB_DOCSTORE_INDEX = config.get('public', 'namesdb_index')

# Filesystem path and URL for static media (mostly used for interfaces).
STATIC_ROOT = config.get('public', 'static_root')
STATIC_URL='/static/'

# Filesystem path and URL for media to be manipulated by ddrlocal
# (collection repositories, thumbnail cache, etc).
MEDIA_ROOT = config.get('public', 'media_root')
MEDIA_URL = config.get('public', 'media_url')
# URL of local media server ("local" = in the same cluster).
# Use this for sorl.thumbnail so it doesn't have to go through
# a CDN and get blocked for not including a User-Agent header.
# TODO Hard-coded! Replace with value from ddr.cfg.
MEDIA_URL_LOCAL = config.get('public', 'media_url_local')
# The REST API will use MEDIA_URL_LOCAL for image URLs
# if this query argument is present with a truthy value.
MEDIA_URL_LOCAL_MARKER = 'internal'

# URL for full-size images and other downloadables.
# Clicking this should bring up the browser's "Save As..." dialog.
# Requires extra config on the web server!
# Nginx example (see https://gist.github.com/un33k/7119264):
#     if ($request_filename ~ "^.*/(.+\.(doc|docx|jpg|jpeg|pdf|tif|tiff|xls))$") {
#       set $fname $1;
#       add_header Content-Disposition 'attachment; filename="$fname"';
#     }
DOWNLOAD_URL = config.get('public', 'download_url')

ACCESS_FILE_APPEND='-a'
ACCESS_FILE_EXTENSION='.jpg'
ACCESS_FILE_GEOMETRY='1024x1024>'
ACCESS_FILE_OPTIONS=''
THUMBNAIL_GEOMETRY='512x512>'
THUMBNAIL_COLORSPACE='sRGB'
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
    'django.contrib.sessions',
    'django.contrib.sites',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.admin',
    #
    'bootstrap_pagination',
    'rest_framework',
    'sorl.thumbnail',
    #
    'ddrpublic',
    'ui',
    'names',
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
ELASTICSEARCH_MAX_SIZE = 1000000
ELASTICSEARCH_QUERY_TIMEOUT = 60 * 10  # 10 min
ELASTICSEARCH_FACETS_TIMEOUT = 60*60*1  # 1 hour

RESULTS_PER_PAGE = 25

# sorl-thumbnail
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.cached_db_kvstore.KVStore'
#THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
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
        ddrfile.identifier.collection_id(),
        ddrfile.parent_id(),
        os.path.basename(ddrfile.access_rel)
    )

# colo
def UI_THUMB_URL(ddrfile):
    """Example:
    /media/ddr-testing-123/ddr-testing-123-1-master-a1b2c3d4e5-a.jpg
    """
    return '%s%s/%s' % (
        MEDIA_URL,
        ddrfile.identifier.collection_id(),
        os.path.basename(ddrfile.access_rel)
    )

# # Amazon S3
# def UI_THUMB_URL(ddrfile):
#     """Example:
#     https://densho-ddr.s3.amazonaws.com/ddr-testing-123/ddr-testing-123-1-master-a1b2c3d4e5-a.jpg
#     """
#     bucket = 'densho-ddr'
#     folder = ddrfile.identifier.collection_id()
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
        filename = ddrfile.identifier.id + extension
        path_rel = os.path.join(ddrfile.identifier.collection_id(), filename)
        url = DOWNLOAD_URL + path_rel
        return url
    return None


#SESSION_ENGINE = 'redis_sessions.session'

TEMPLATE_DIRS = (
    '/usr/local/src/ddr-public/ddrpublic/names/templates',
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
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/ddr/public.log',
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
    'ui.context_processors.sitewide',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ui.urls'

WSGI_APPLICATION = 'ddrpublic.wsgi.application'
