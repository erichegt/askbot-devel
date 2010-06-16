import re

def get_from_dict_or_object(source, key):
    try:
        return source[key]
    except:
        return getattr(source,key)


def is_iterable(thing):
    if hasattr(thing, '__iter__'):
        return True
    else:
        return isinstance(thing, basestring)

BOT_REGEX = re.compile(
    r'bot|http|\.com|crawl|spider|python|curl|yandex'
)
BROWSER_REGEX = re.compile(
    r'^(Mozilla.*(Gecko|KHTML|MSIE|Presto|Trident)|Opera).*$'
)
MOBILE_REGEX = re.compile(
    r'(BlackBerry|HTC|LG|MOT|Nokia|NOKIAN|PLAYSTATION|PSP|SAMSUNG|SonyEricsson)'
)


def not_a_robot_request(request):

    if 'HTTP_ACCEPT_LANGUAGE' not in request.META:
        return False

    user_agent = request.META.get('HTTP_USER_AGENT', None)
    if user_agent is None:
        return False

    if BOT_REGEX.match(user_agent, re.IGNORECASE):
        return False

    if MOBILE_REGEX.match(user_agent):
        return True

    if BROWSER_REGEX.search(user_agent):
        return True

    return False
