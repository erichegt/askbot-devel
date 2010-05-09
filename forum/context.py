from django.conf import settings
from forum.conf import settings as forum_settings
def application_settings(context):
    my_settings = {
        'WIKI_ON':forum_settings.WIKI_ON,
        'APP_TITLE' : forum_settings.APP_TITLE,
        'APP_URL'   : forum_settings.APP_URL,
        'APP_KEYWORDS' : forum_settings.APP_KEYWORDS,
        'APP_DESCRIPTION': forum_settings.APP_DESCRIPTION,
        'APP_COPYRIGHT': forum_settings.APP_COPYRIGHT,
        'FEEDBACK_SITE_URL': forum_settings.FEEDBACK_SITE_URL,
        'FORUM_ABOUT': forum_settings.FORUM_ABOUT,
        'FORUM_PRIVACY': forum_settings.FORUM_PRIVACY,
        'GOOGLE_SITEMAP_CODE':forum_settings.GOOGLE_VERIFICATION_CODE,
        'GOOGLE_ANALYTICS_KEY':forum_settings.GOOGLE_ANALYTICS_KEY,
        'RESOURCE_REVISION':settings.RESOURCE_REVISION,
        'ASKBOT_SKIN':settings.ASKBOT_DEFAULT_SKIN,
        'EMAIL_VALIDATION': settings.EMAIL_VALIDATION,
        'FORUM_SCRIPT_ALIAS': settings.FORUM_SCRIPT_ALIAS,
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
        'EDITABLE_SCREEN_NAME':settings.EDITABLE_SCREEN_NAME,
        }
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
