"""Askbot template context processor that makes some parameters
from the django settings, all parameters from the askbot livesettings
and the application available for the templates
"""
import sys
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.utils.translation import get_language

import askbot
from askbot import api
from askbot import models
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.skins.loaders import get_skin
from askbot.utils import url_utils
from askbot.utils.slug import slugify

def application_settings(request):
    """The context processor function"""
    if not request.path.startswith('/' + settings.ASKBOT_URL):
        #todo: this is a really ugly hack, will only work
        #when askbot is installed not at the home page.
        #this will not work for the
        #heavy modders of askbot, because their custom pages
        #will not receive the askbot settings in the context
        #to solve this properly we should probably explicitly
        #add settings to the context per page
        return {}
    my_settings = askbot_settings.as_dict()
    my_settings['LANGUAGE_CODE'] = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    my_settings['MULTILINGUAL'] = getattr(settings, 'ASKBOT_MULTILINGUAL', False)
    my_settings['LANGUAGES_DICT'] = dict(getattr(settings, 'LANGUAGES', []))
    my_settings['ALLOWED_UPLOAD_FILE_TYPES'] = \
            settings.ASKBOT_ALLOWED_UPLOAD_FILE_TYPES
    my_settings['ASKBOT_URL'] = settings.ASKBOT_URL
    my_settings['STATIC_URL'] = settings.STATIC_URL
    my_settings['ASKBOT_CSS_DEVEL'] = getattr(
                                        settings,
                                        'ASKBOT_CSS_DEVEL',
                                        False
                                    )
    my_settings['USE_LOCAL_FONTS'] = getattr(
                                        settings,
                                        'ASKBOT_USE_LOCAL_FONTS',
                                        False
                                    )
    my_settings['DEBUG'] = settings.DEBUG
    my_settings['USING_RUNSERVER'] = 'runserver' in sys.argv
    my_settings['ASKBOT_VERSION'] = askbot.get_version()
    my_settings['LOGIN_URL'] = url_utils.get_login_url()
    my_settings['LOGOUT_URL'] = url_utils.get_logout_url()
    my_settings['LOGOUT_REDIRECT_URL'] = url_utils.get_logout_redirect_url()
    my_settings['USE_ASKBOT_LOGIN_SYSTEM'] = 'askbot.deps.django_authopenid' \
        in settings.INSTALLED_APPS
    context = {
        'current_language_code': get_language(),
        'settings': my_settings,
        'skin': get_skin(request),
        'moderation_items': api.get_info_on_moderation_items(request.user),
        'noscript_url': const.DEPENDENCY_URLS['noscript'],
    }

    if askbot_settings.GROUPS_ENABLED:
        #calculate context needed to list all the groups
        def _get_group_url(group):
            """calculates url to the group based on its id and name"""
            group_slug = slugify(group['name'])
            return reverse(
                'users_by_group',
                kwargs={'group_id': group['id'], 'group_slug': group_slug}
            )

        #load id's and names of all groups
        global_group = models.Group.objects.get_global_group()
        groups = models.Group.objects.exclude_personal()
        groups = groups.exclude(id=global_group.id)
        groups_data = list(groups.values('id', 'name'))

        #sort groups_data alphanumerically, but case-insensitive
        groups_data = sorted(
                        groups_data,
                        lambda x, y: cmp(x['name'].lower(), y['name'].lower())
                    )

        #insert data for the global group at the first position
        groups_data.insert(0, {'id': global_group.id, 'name': global_group.name})

        #build group_list for the context
        group_list = list()
        for group in groups_data:
            link = _get_group_url(group)
            group_list.append({'name': group['name'], 'link': link})
        context['group_list'] = simplejson.dumps(group_list)

    return context
