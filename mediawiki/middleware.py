from django.contrib import auth
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
import logging
import traceback
import sys

class IncludeVirtualAuthenticationMiddleware(object):
    def process_request(self,request):
        """in this type of authentication the mw session token is passed via
        "session" request parameter and authentication happens on every
        request
        """
        logging.debug('trying include virtual milldeware')
        if not hasattr(request,'user'):
            raise ImproperlyConfigured(
                "The include virtual mediawiki authentication middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the IncludeVirtualAuthenticationMiddleware class."
            )

        session = None
        request.is_include_virtual = False
        if request.is_ajax():
            logging.debug('have ajax request')
            cookie_name = settings.MEDIAWIKI_SESSION_COOKIE_NAME
            if cookie_name in request.COOKIES:
                session = request.COOKIES[cookie_name]
                logging.debug('ajax call has session %s' % session)
            else:
                logging.debug('dont have cookie')
        else:
            if request.REQUEST.has_key('session'):
                session = request.REQUEST['session']
                request.is_include_virtual = True
                logging.debug('I am virtual')
                if request.REQUEST.get('was_posted','false') == 'true':
                    data = request.GET.copy()
                    data['recaptcha_ip_field'] = request.META['REMOTE_ADDR']
                    request.GET = data
                    logging.debug('REQUEST is now %s' % str(request.GET))
        user = auth.authenticate(token=session) #authenticate every time
        if user:
            request.user = user
            auth.login(request,user)
        #else I probably need to forbid access
        #raise ImproperlyConfigured(
        #    "The include virtual mediawiki authentication middleware requires the"
        #    "'session' request parameter set in the including document"
        #)

    def process_exception(self,request,exception):
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        logging.debug('\n'.join(traceback.format_tb(exceptionTraceback)))
        logging.debug('have exception %s %s' % (exceptionType,exceptionValue))
