from django.conf import settings
from django.template import loader
from django.template.loaders import filesystem 
from django.http import HttpResponse
import os.path
import logging

#module for skinning osqa
#at this point skin can be changed only in settings file
#via OSQA_DEFAULT_SKIN variable

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths

def load_template_source(name, dirs=None):
    try:
        tname = os.path.join(settings.OSQA_DEFAULT_SKIN,'templates',name)
        return filesystem.load_template_source(tname,dirs)
    except:
        tname = os.path.join('default','templates',name)
        return filesystem.load_template_source(tname,dirs)
load_template_source.is_usable = True

def find_media_source(url):
    """returns url prefixed with the skin name
    of the first skin that contains the file 
    directories are searched in this order:
    settings.OSQA_DEFAULT_SKIN, then 'default', then 'commmon'
    if file is not found - returns None
    and logs an error message
    """
    while url[0] == '/': url = url[1:]
    d = os.path.dirname
    n = os.path.normpath
    j = os.path.join
    f = os.path.isfile
    skins = n(j(d(d(__file__)),'skins'))
    try:
        media = os.path.join(skins, settings.OSQA_DEFAULT_SKIN, url)
        assert(f(media))
        use_skin = settings.OSQA_DEFAULT_SKIN
    except:
        try:
            media = j(skins, 'default', url)
            assert(f(media))
            use_skin = 'default'
        except:
            media = j(skins, 'common', url)
            try:
                assert(f(media))
                use_skin = 'common'
            except:
                logging.error('could not find media for %s' % url)
                use_skin = ''
                return None
    return use_skin + '/' + url
