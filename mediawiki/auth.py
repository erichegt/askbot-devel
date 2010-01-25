from mediawiki.models import User as MWUser
from django.contrib.auth.models import User
from django_authopenid.models import ExternalLoginData
from django.conf import settings
import logging
from PHPUnserialize import PHPUnserialize
import os

class php(object):
    @staticmethod
    def get_session_data(session):
        prefix = settings.MEDIAWIKI_PHP_SESSION_PREFIX
        path = settings.MEDIAWIKI_PHP_SESSION_PATH
        file = os.path.join(path,prefix + session)
        #file may not exist
        data = open(file).read() 
        u = PHPUnserialize()
        return u.session_decode(data)

class IncludeVirtualAuthenticationBackend(object):
    def authenticate(self,token=None):
        logging.debug('authenticating session %s' % token)
        try:
            php_session = php.get_session_data(token)
        #todo: report technical errors to root
        except:
            #Fail condition 1. Session data cannot be retrieved
            logging.debug('session %s cannot be retrieved' % str(token))
            return None
        try:
            name = php_session['wsUserName']
            id = php_session['wsUserID']
        except:
            #Fail condition 2. Data misses keys
            logging.debug('missing data in session table')
            return None
        try:
            logging.debug('trying to find user %s id=%s in the MW database' % (name,id))
            wu = MWUser.objects.get(user_name=name,user_id=id)
        except MWUser.DoesNotExist:
            #Fail condition 3. User does not match session data
            logging.debug('could not find wiki user who owns session')
            return None
        try:
            logging.debug('trying to get external login data for mw user %s' % name)
            eld = ExternalLoginData.objects.get(external_username=name)
            #update session data and save?
            return eld.user #may be none!
        except ExternalLoginData.DoesNotExist:
            #Fail condition 4. no external login data - user never logged in through django
            #using the wiki login and password
            logging.debug('no association found for MW user %s with django user' % name)
            return None
                
    def get_user(self, user_id):    
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
