from django.template import loader
from django.template.loaders import filesystem 
import os.path
import os
import logging
from forum.conf import settings as forum_settings
from forum.skins import utils

#module for skinning askbot
#via ASKBOT_DEFAULT_SKIN configureation variable (not django setting)

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths

def load_template_source(name, dirs=None):
    print 'want template %s' % name
    try:
        #todo: move this to top after splitting out get_skin_dirs()
        print 'trying to import forum_settings'
        print 'imported!'
        tname = os.path.join(forum_settings.ASKBOT_DEFAULT_SKIN,'templates',name)
        print tname
        print 'success'
        return filesystem.load_template_source(tname,dirs)
    except:
        print 'failed'
        tname = os.path.join('default','templates',name)
        return filesystem.load_template_source(tname,dirs)
load_template_source.is_usable = True

def find_media_source(url):
    """returns url prefixed with the skin name
    of the first skin that contains the file 
    directories are searched in this order:
    forum_settings.ASKBOT_DEFAULT_SKIN, then 'default', then 'commmon'
    if file is not found - returns None
    and logs an error message
    """
    print 'trying to get source dammit'
    while url[0] == '/': url = url[1:]
    d = os.path.dirname
    n = os.path.normpath
    j = os.path.join
    f = os.path.isfile
    #todo: handles case of multiple skin directories
    skins = utils.get_skin_dirs()[0]
    try:
        #todo: move this to top after splitting out get_skin_dirs()
        print 'looking for the media path'
        media = os.path.join(skins, forum_settings.ASKBOT_DEFAULT_SKIN, url)
        print 'out of dadata'
        assert(f(media))
        use_skin = forum_settings.ASKBOT_DEFAULT_SKIN
    except:
        print 'failed'
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
