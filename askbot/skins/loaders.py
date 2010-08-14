from django.template import loader
from django.template.loaders import filesystem
import os.path
import os
import logging
from askbot.skins import utils
from askbot.conf import settings as askbot_settings

#module for skinning askbot
#via ASKBOT_DEFAULT_SKIN configureation variable (not django setting)

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths
ASKBOT_SKIN_COLLECTION_DIR = os.path.dirname(__file__)

def load_template_source(name, dirs=None):
    if dirs is None:
        dirs = (ASKBOT_SKIN_COLLECTION_DIR, )
    else:
        dirs += (ASKBOT_SKIN_COLLECTION_DIR, )

    try:
        #todo: move this to top after splitting out get_skin_dirs()
        tname = os.path.join(askbot_settings.ASKBOT_DEFAULT_SKIN,'templates',name)
        return filesystem.load_template_source(tname,dirs)
    except:
        tname = os.path.join('default','templates',name)
        return filesystem.load_template_source(tname,dirs)
load_template_source.is_usable = True
