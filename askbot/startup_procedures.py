"""tests to be performed
in the beginning of models/__init__.py

the purpose of this module is to validate deployment of askbot

question: why not run these from askbot/__init__.py?

the main function is run_startup_tests
"""
import sys
from django.db import transaction
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from askbot.models import badges
from askbot.utils.loading import load_module

PREAMBLE = """\n
************************
*                      *
*   Askbot self-test   *
*                      *
************************"""

def format_as_text_tuple_entries(items):
    """prints out as entries or tuple containing strings
    ready for copy-pasting into say django settings file"""
    return "    '%s'," % "',\n    '".join(items)

#todo:
#
# *validate emails in settings.py
def test_askbot_url():
    """Tests the ASKBOT_URL setting for the 
    well-formedness and raises the ImproperlyConfigured
    exception, if the setting is not good.
    """
    url = django_settings.ASKBOT_URL
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

def test_middleware():
    """Checks that all required middleware classes are
    installed in the django settings.py file. If that is not the
    case - raises an ImproperlyConfigured exception.
    """
    required_middleware = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
        'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
        'askbot.middleware.cancel.CancelActionMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
        'askbot.middleware.view_log.ViewLogMiddleware',
    )
    if 'debug_toolbar' in django_settings.INSTALLED_APPS:
        required_middleware += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

    installed_middleware_set = set(django_settings.MIDDLEWARE_CLASSES)
    missing_middleware_set = set(required_middleware) - installed_middleware_set

    if missing_middleware_set:
        error_message = """\n\nPlease add the following middleware (listed after this message)
to the MIDDLEWARE_CLASSES variable in your site settings.py file. 
The order the middleware records may be important, please take a look at the example in 
https://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/settings.py:\n\n"""
        middleware_text = format_as_text_tuple_entries(missing_middleware_set)
        raise ImproperlyConfigured(PREAMBLE + error_message + middleware_text)


    #middleware that was used in the past an now removed
    canceled_middleware = (
        'askbot.deps.recaptcha_django.middleware.ReCaptchaMiddleware',
    )
    #'debug_toolbar.middleware.DebugToolbarMiddleware',

    remove_middleware_set = set(canceled_middleware) & installed_middleware_set
    if remove_middleware_set:
        error_message = """\n\nPlease remove the following middleware entries from
the list of MIDDLEWARE_CLASSES in your settings.py - these are not used any more:\n\n"""
        middleware_text = format_as_text_tuple_entries(remove_middleware_set)
        raise ImproperlyConfigured(PREAMBLE + error_message + middleware_text)

            

def test_i18n():
    if getattr(django_settings, 'USE_I18N', False) == False:
        raise ImproperlyConfigured(
            'Please set USE_I18N = True in settings.py and '
            'set the LANGUAGE_CODE parameter correctly '
            'it is very important for askbot.'
        )

def try_import(module_name, pypi_package_name):
    try:
        load_module(module_name)
    except ImportError, e:
        message = unicode(e) + ' run\npip install %s' % pypi_package_name
        message += '\nTo install all the dependencies at once, type:'
        message += '\npip install -r askbot_requirements.txt\n'
        raise ImproperlyConfigured(message)

def test_modules():
    try_import('recaptcha_works', 'django-recaptcha-works')

def run_startup_tests():
    """function that runs
    all startup tests, mainly checking settings config so far
    """

    #todo: refactor this when another test arrives
    test_modules()
    test_askbot_url()
    test_i18n()
    test_middleware()

@transaction.commit_manually
def run():
    """runs all the startup procedures"""
    run_startup_tests()
    try:
        badges.init_badges()
        transaction.commit()
    except:
        transaction.rollback()
