import os.path
from django.template.loaders import filesystem
from django.utils import translation
from askbot.conf import settings as askbot_settings
from django.conf import settings as django_settings
from coffin.common import CoffinEnvironment
from jinja2 import loaders as jinja_loaders
from askbot.skins import utils

#module for skinning askbot
#via ASKBOT_DEFAULT_SKIN configureation variable (not django setting)

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths
ASKBOT_SKIN_COLLECTION_DIR = os.path.dirname(__file__)

def load_template_source(name, dirs=None):
    """Django template loader
    """
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

class SkinEnvironment(CoffinEnvironment):
    """Jinja template environment
    that loads templates from askbot skins
    """

    def _get_loaders(self):
        """over-ridden function _get_loaders that creates
        the loader for the skin templates
        """
        loaders = list()
        skin_name = askbot_settings.ASKBOT_DEFAULT_SKIN
        skin_dirs = utils.get_available_skins(selected = skin_name).values()
        template_dirs = [os.path.join(skin_dir, 'templates') for skin_dir in skin_dirs]

        loaders.append(jinja_loaders.FileSystemLoader(template_dirs))
        return loaders

    def set_language(self, language_code):
        """hooks up translation objects from django to jinja2
        environment.
        note: not so sure about thread safety here
        """
        trans = translation.trans_real.translation(language_code)
        self.install_gettext_translations(trans)


ENV = SkinEnvironment(autoescape=False, extensions=['jinja2.ext.i18n'])
ENV.set_language(django_settings.LANGUAGE_CODE)
