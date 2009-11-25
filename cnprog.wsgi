import os
import sys
sys.path.append('/path/above_forum')
sys.path.append('/path/above_forum/forum_dir')
os.environ['DJANGO_SETTINGS_MODULE'] = 'forum_dir.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
