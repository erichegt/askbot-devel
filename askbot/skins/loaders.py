import os.path
from django.template.loaders import filesystem
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import translation
from askbot.conf import settings as askbot_settings
from django.conf import settings as django_settings
from coffin.common import CoffinEnvironment
from jinja2 import loaders as jinja_loaders
from jinja2.exceptions import TemplateNotFound
from jinja2.utils import open_if_exists
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

class SkinLoader(jinja_loaders.BaseLoader):
    """loads template from the skin directory
    code largely copy-pasted from the jinja2 internals
    """
    def get_source(self, environment, template):
        pieces = jinja_loaders.split_template_path(template)
        skin = askbot_settings.ASKBOT_DEFAULT_SKIN
        skin_path = utils.get_path_to_skin(skin)
        filename = os.path.join(skin_path, 'templates', *pieces)
        print 'want file %s' % filename
        f = open_if_exists(filename)
        if f is None:
            raise TemplateNotFound(template)
        try:
            contents = f.read().decode('utf-8')
        finally:
            f.close()

        mtime = os.path.getmtime(filename)
        def uptodate():
            try:
                return os.path.getmtime(filename) == mtime
            except OSError:
                return False
        return contents, filename, uptodate

class SkinEnvironment(CoffinEnvironment):
    """Jinja template environment
    that loads templates from askbot skins
    """

    def __init__(self, *args, **kwargs):
        """save the skin path and initialize the
        Coffin Environment
        """
        self.skin = kwargs.pop('skin')
        super(SkinEnvironment, self).__init__(*args, **kwargs)

    def _get_loaders(self):
        """this method is not used
        over-ridden function _get_loaders that creates
        the loader for the skin templates
        """
        loaders = list()
        skin_dirs = utils.get_available_skins(selected = self.skin).values()
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

    def get_extra_css_link(self):
        """returns either the link tag (to be inserted in the html head element)
        or empty string - depending on the existence of file
        SKIN_PATH/media/style/extra.css
        """
        url = utils.get_media_url('style/extra.css')
        if url is not None:
            return '<link href="%s" rel="stylesheet" type="text/css" />' % url
        return ''

ENV = SkinEnvironment(
            autoescape=False,
            extensions=['jinja2.ext.i18n'],
            skin = askbot_settings.ASKBOT_DEFAULT_SKIN
            #loader = SkinLoader()
         )
ENV.set_language(django_settings.LANGUAGE_CODE)

def load_skins():
    skins = dict()
    for skin_name in utils.get_available_skins():
        skins[skin_name] = SkinEnvironment(skin = skin_name)
        skins[skin_name].set_language(django_settings.LANGUAGE_CODE)
    return skins

SKINS = load_skins()

def get_skin(request):
    """retreives the skin environment
    for a given request (request var is not used at this time)"""
    return SKINS[askbot_settings.ASKBOT_DEFAULT_SKIN]

def get_template(template, request):
    """retreives template for the skin
    request variable will be used in the future to set
    template according to the user preference or admins preference

    at this point request variable is not used though
    """
    skin = get_skin(request)
    return skin.get_template(template)

def render_into_skin(template, data, request, mimetype = 'text/html'):
    """in the future this function will be able to
    switch skin depending on the site administrator/user selection
    right now only admins can switch
    """
    context = RequestContext(request, data)
    template = get_template(template, request)
    return HttpResponse(template.render(context), mimetype = mimetype)
