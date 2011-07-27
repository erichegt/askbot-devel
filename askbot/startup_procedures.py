"""tests to be performed
in the beginning of models/__init__.py

the purpose of this module is to validate deployment of askbot

question: why not run these from askbot/__init__.py?

the main function is run_startup_tests
"""
from django.db import transaction
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from askbot.models import badges

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
        'askbot.middleware.anon_user.ConnectToSessionMessagesMiddleware',
        'askbot.middleware.pagesize.QuestionsPageSizeMiddleware',
        'askbot.middleware.cancel.CancelActionMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
        'askbot.middleware.view_log.ViewLogMiddleware',
    )
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    missing_middleware = list()
    for middleware in required_middleware:
        if middleware not in django_settings.MIDDLEWARE_CLASSES:
            missing_middleware.append(middleware)

    debug_toolbar_middleware = 'debug_toolbar.middleware.DebugToolbarMiddleware'
    if 'debug_toolbar' in django_settings.INSTALLED_APPS:
        if debug_toolbar_middleware not in django_settings.MIDDLEWARE_CLASSES:
            missing_middleware.append(debug_toolbar_middleware)

    if missing_middleware:
        error_message = """Please add the following middleware (listed 
after this message) to the MIDDLEWARE_CLASSES variable in your site settings.py file. 
The order the middleware records may be important, please take a look at the example in 
https://github.com/ASKBOT/askbot-devel/blob/master/askbot/setup_templates/settings.jy\n\n%s""" \
        % ', '.join(missing_middleware)
        raise ImproperlyConfigured(error_message)

def test_i18n():
    if getattr(django_settings, 'USE_I18N', False) == False:
        raise ImproperlyConfigured(
            'Please set USE_I18N = True in settings.py and '
            'set the LANGUAGE_CODE parameter correctly '
            'it is very important for askbot.'
        )

def run_startup_tests():
    """function that runs
    all startup tests, mainly checking settings config so far
    """

    #todo: refactor this when another test arrives
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
