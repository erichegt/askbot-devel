from django.conf import settings
from askbot.conf import settings as askbot_settings
import datetime

def application_settings(context):
    my_settings = askbot_settings.as_dict()
    my_settings['LANGUAGE_CODE'] = settings.LANGUAGE_CODE
    my_settings['ASKBOT_URL'] = settings.ASKBOT_URL
    return {'settings':my_settings}

def auth_processor(request):
    """
    Returns context variables required by apps that use Django's authentication
    system.

    If there is no 'user' attribute in the request, uses AnonymousUser (from
    django.contrib.auth).
    """
    if hasattr(request, 'user'):
        user = request.user
        if user.is_authenticated():
            messages = user.message_set.all()
        else:
            messages = None
    else:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        messages = None

    from django.core.context_processors import PermWrapper
    return {
        'user': user,
        'messages': messages,
        'perms': PermWrapper(user),
    }
