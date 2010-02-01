import os
import sys
sys.path.append('/usr/local/sites/osqa_staging')
sys.path.append('/usr/local/sites/osqa_staging/robofaqs')
os.environ['DJANGO_SETTINGS_MODULE'] = 'robofaqs.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
