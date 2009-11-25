# encoding:utf-8
# Django settings for lanai project.
import os.path
import sys

SITE_ID = 1

ADMIN_MEDIA_PREFIX = '/forum/admin/media/'
SECRET_KEY = '$oo^&_m&qwbib=(_4m_n*zn-d=g#s0he5fx9xonnym#8p6yigm'
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    #'django.middleware.sqlprint.SqlPrintingMiddleware',
    'middleware.anon_user.ConnectToSessionMessagesMiddleware',
    'middleware.pagesize.QuestionsPageSizeMiddleware',
    'middleware.cancel.CancelActionMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'context.application_settings',
    #'django.core.context_processors.i18n',
    'user_messages.context_processors.user_messages',#must be before auth
    'django.core.context_processors.auth', #this is required for admin
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates').replace('\\','/'),
)

#UPLOAD SETTINGS
FILE_UPLOAD_TEMP_DIR = os.path.join(os.path.dirname(__file__), 'tmp').replace('\\','/')
FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.MemoryFileUploadHandler",
 "django.core.files.uploadhandler.TemporaryFileUploadHandler",)
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# for user upload
ALLOW_FILE_TYPES = ('.jpg', '.jpeg', '.gif', '.bmp', '.png', '.tiff')
# unit byte
ALLOW_MAX_FILE_SIZE = 1024 * 1024

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'forum',
    'django_authopenid',
    'djangosphinx',
    #'debug_toolbar' ,
    'user_messages',
)

# User settings
from settings_local import *
