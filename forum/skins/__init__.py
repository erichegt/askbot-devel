from django.template import loader
from django.template.loaders import filesystem 
from django.http import HttpResponse
import os.path
import os
import logging

#module for skinning askbot
#via ASKBOT_DEFAULT_SKIN configureation variable (not django setting)

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths

def load_template_source(name, dirs=None):
    try:
        #todo: move this to top after splitting out get_skin_dirs()
        from forum.conf import settings as forum_settings
        tname = os.path.join(forum_settings.ASKBOT_DEFAULT_SKIN,'templates',name)
        return filesystem.load_template_source(tname,dirs)
    except:
        tname = os.path.join('default','templates',name)
        return filesystem.load_template_source(tname,dirs)
load_template_source.is_usable = True

#todo: move this to skins/utils.py
#then move import forum.conf.settings to top
def get_skin_dirs():
    #todo: handle case of multiple skin directories
    d = os.path.dirname
    n = os.path.normpath
    j = os.path.join
    f = os.path.isfile
    skin_dirs = []
    skin_dirs.append( n(j(d(d(__file__)), 'skins')) )
    return skin_dirs

def find_media_source(url):
    """returns url prefixed with the skin name
    of the first skin that contains the file 
    directories are searched in this order:
    forum_settings.ASKBOT_DEFAULT_SKIN, then 'default', then 'commmon'
    if file is not found - returns None
    and logs an error message
    """
    while url[0] == '/': url = url[1:]
    d = os.path.dirname
    n = os.path.normpath
    j = os.path.join
    f = os.path.isfile
    #todo: handles case of multiple skin directories
    skins = get_skin_dirs()[0]
    try:
        #todo: move this to top after splitting out get_skin_dirs()
        from forum.conf import settings as forum_settings
        media = os.path.join(skins, forum_settings.ASKBOT_DEFAULT_SKIN, url)
        assert(f(media))
        use_skin = forum_settings.ASKBOT_DEFAULT_SKIN
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

def get_skin_choices():
    #todo: expand this to handle custom skin directories
    dirs = get_skin_dirs()
    default_dir = dirs[0]
    items = os.listdir(default_dir)
    skin_list = ['default']
    for i in items:
        item_path = os.path.join(default_dir,i)
        if not os.path.isdir(item_path):
            continue
        if i == 'common':
            continue
        if i not in skin_list:
            skin_list.append(i)

    return [(i,i) for i in skin_list]
