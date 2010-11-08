from django.conf import settings
from askbot.conf import settings as askbot_settings
from askbot import api
import datetime

def application_settings(request):
    my_settings = askbot_settings.as_dict()
    my_settings['LANGUAGE_CODE'] = settings.LANGUAGE_CODE
    my_settings['ASKBOT_URL'] = settings.ASKBOT_URL
    return {
        'settings': my_settings,
        'moderation_items': api.get_info_on_moderation_items(request.user)
    }
