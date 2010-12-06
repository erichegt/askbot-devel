"""tests to be performed
in the beginning of models/__init__.py

the purpose of this module is to validate deployment of askbot

the main function is run_startup_tests
"""
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from askbot.models import badges

#todo:
#
# *validate emails in settings.py

def run_startup_tests():
    """function that runs
    all startup tests, mainly checking settings config so far
    """

    #todo: refactor this when another test arrives
    url = settings.ASKBOT_URL
    if url != '':

        if isinstance(url, str) or isinstance(url, unicode):
            pass
        else:
            msg = 'setting ASKBOT_URL must be of string or unicode type'
            raise ImproperlyConfigured(msg)

        if url == '/':
            msg = 'value "/" for ASKBOT_URL is invalid. '+ \
                'Please, either make ASKBOT_URL an empty string ' + \
                'or a non-empty path, ending with "/" but not ' + \
                'starting with "/", for example: "forum/"'
            raise ImproperlyConfigured(msg)
        else:
            try:
                assert(url.endswith('/'))
            except AssertionError:
                msg = 'if ASKBOT_URL setting is not empty, ' + \
                        'it must end with /'
                raise ImproperlyConfigured(msg)
            try:
                assert(not url.startswith('/'))
            except AssertionError:
                msg = 'if ASKBOT_URL setting is not empty, ' + \
                        'it must not start with /'

@transaction.commit_manually
def run():
    """runs all the startup procedures"""
    run_startup_tests()
    try:
        badges.init_badges()
        transaction.commit()
    except:
        transaction.rollback()
