"""Askbot template context processor that makes some parameters
from the django settings, all parameters from the askbot livesettings
and the application available for the templates
"""
from django.conf import settings
import askbot
from askbot import api
from askbot.conf import settings as askbot_settings

def application_settings(request):
    """The context processor function"""
    my_settings = askbot_settings.as_dict()
    my_settings['LANGUAGE_CODE'] = settings.LANGUAGE_CODE
    my_settings['ASKBOT_URL'] = settings.ASKBOT_URL
    my_settings['DEBUG'] = settings.DEBUG
    my_settings['ASKBOT_VERSION'] = askbot.get_version()
    return {
        'settings': my_settings,
        'moderation_items': api.get_info_on_moderation_items(request.user)
    }
