import os
import sys
sys.path.append('/var/www/vhosts/default/htdocs')
sys.path.append('/var/www/vhosts/default/htdocs/forum')
os.environ['DJANGO_SETTINGS_MODULE'] = 'forum.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
