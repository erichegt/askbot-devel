"""functions in this module return body text
of email messages for various occasions
"""
import functools
from django.template import Context
from django.template.loader import get_template
from askbot.conf import settings as askbot_settings
from askbot.utils import html as html_utils

def message(template = None):
    """a decorator that creates a function
    which returns formatted message using the
    template and data"""
    def decorate(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            template_object = get_template(template)
            data = func(*args, **kwargs)
            return template_object.render(Context(data))#todo: set lang
        return wrapped
    return decorate

@message(template = 'email/ask_for_signature.html')
def ask_for_signature(user, footer_code = None):
    """tells that we don't have user's signature
    and because of that he/she cannot make posts
    the message will ask to make a simple response
    """
    return {
        'username': user.username,
        'site_name': askbot_settings.APP_SHORT_NAME,
        'footer_code': footer_code
    }

@message(template = 'email/notify_admins_about_new_tags.html')
def notify_admins_about_new_tags(
    tags = None, thread = None, user = None
):
    thread_url = thread.get_absolute_url()
    return {
        'thread_url': html_utils.site_url(thread_url),
        'tags': tags,
        'user': user
    }

@message(template = 'email/insufficient_rep_to_post_by_email.html')
def insufficient_reputation(user):
    """tells user that he does not have
    enough rep and suggests to ask on the web
    """
    min_rep = askbot_settings.MIN_REP_TO_POST_BY_EMAIL
    min_upvotes = 1 + \
        (min_rep/askbot_settings.REP_GAIN_FOR_RECEIVING_UPVOTE)
    site_link = html_utils.site_link(
        'ask',
        askbot_settings.APP_SHORT_NAME
    )
    return {
        'username': user.username,
        'site_name': askbot_settings.APP_SHORT_NAME,
        'site_link': site_link,
        'min_upvotes': min_upvotes
    }
