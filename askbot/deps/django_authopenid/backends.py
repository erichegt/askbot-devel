"""authentication backend that takes care of the
multiple login methods supported by the authenticator
application
"""
import datetime
import logging
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from askbot.deps.django_authopenid.models import UserAssociation
from askbot.deps.django_authopenid import util

class AuthBackend(object):
    """Authenticator's authentication backend class
    for more info, see django doc page:
    http://docs.djangoproject.com/en/dev/topics/auth/#writing-an-authentication-backend

    the reason there is only one class - for simplicity of
    adding this application to a django project - users only need
    to extend the AUTHENTICATION_BACKENDS with a single line
    """

    def authenticate(
                self,
                username = None,#for 'password'
                password = None,#for 'password'
                user_id = None,#for 'force'
                provider_name = None,#required with all except email_key
                openid_url = None,
                email_key = None,
                oauth_user_id = None,#used with oauth
                facebook_user_id = None,#user with facebook
                ldap_user_id = None,#for ldap
                wordpress_url = None, # required for self hosted wordpress
                wp_user_id = None, # required for self hosted wordpress
                method = None,#requried parameter
            ):
        """this authentication function supports many login methods
        just which method it is going to use it determined
        from the signature of the function call
        """
        login_providers = util.get_enabled_login_providers()
        if method == 'password':
            if login_providers[provider_name]['type'] != 'password':
                raise ImproperlyConfigured('login provider must use password')
            if provider_name == 'local':
                try:
                    user = User.objects.get(username=username)
                    if not user.check_password(password):
                        return None
                except User.DoesNotExist:
                    try:
                        email_address = username
                        user = User.objects.get(email = email_address)
                        if not user.check_password(password):
                            return None
                    except User.DoesNotExist:
                        return None
                    except User.MultipleObjectsReturned:
                        logging.critical(
                            ('have more than one user with email %s ' +
                            'he/she will not be able to authenticate with ' +
                            'the email address in the place of user name') % email_address
                        )
                        return None
            else:
                if login_providers[provider_name]['check_password'](username, password):
                    try:
                        #if have user associated with this username and provider,
                        #return the user
                        assoc = UserAssociation.objects.get(
                                        openid_url = username + '@' + provider_name,#a hack - par name is bad
                                        provider_name = provider_name
                                    )
                        return assoc.user
                    except UserAssociation.DoesNotExist:
                        #race condition here a user with this name may exist
                        user, created = User.objects.get_or_create(username = username)
                        if created:
                            user.set_password(password)
                            user.save()
                        else:
                            #have username collision - so make up a more unique user name
                            #bug: - if user already exists with the new username - we are in trouble
                            new_username = '%s@%s' % (username, provider_name)
                            user = User.objects.create_user(new_username, '', password)
                            message = _(
                                'Welcome! Please set email address (important!) in your '
                                'profile and adjust screen name, if necessary.'
                            )
                            user.message_set.create(message = message)
                else:
                    return None

            #this is a catch - make login token a little more unique
            #for the cases when passwords are the same for two users
            #from the same provider
            try:
                assoc = UserAssociation.objects.get(
                                            user = user,
                                            provider_name = provider_name
                                        )
            except UserAssociation.DoesNotExist:
                assoc = UserAssociation(
                                    user = user,
                                    provider_name = provider_name
                                )
            assoc.openid_url = username + '@' + provider_name#has to be this way for external pw logins

        elif method == 'openid':
            provider_name = util.get_provider_name(openid_url)
            try:
                assoc = UserAssociation.objects.get(
                                            openid_url = openid_url,
                                            provider_name = provider_name
                                        )
                user = assoc.user
            except UserAssociation.DoesNotExist:
                return None

        elif method == 'email':
            #with this method we do no use user association
            try:
                #todo: add email_key_timestamp field
                #and check key age
                user = User.objects.get(email_key = email_key)
                user.email_key = None #one time key so delete it
                user.email_isvalid = True
                user.save()
                return user
            except User.DoesNotExist:
                return None

        elif method == 'oauth':
            if login_providers[provider_name]['type'] == 'oauth':
                try:
                    assoc = UserAssociation.objects.get(
                                                openid_url = oauth_user_id,
                                                provider_name = provider_name
                                            )
                    user = assoc.user
                except UserAssociation.DoesNotExist:
                    return None
            else:
                return None

        elif method == 'facebook':
            try:
                #assert(provider_name == 'facebook')
                assoc = UserAssociation.objects.get(
                                            openid_url = facebook_user_id,
                                            provider_name = 'facebook'
                                        )
                user = assoc.user
            except UserAssociation.DoesNotExist:
                return None

        elif method == 'ldap':
            try:
                assoc = UserAssociation.objects.get(
                                            openid_url = ldap_user_id,
                                            provider_name = provider_name
                                        )
                user = assoc.user
            except UserAssociation.DoesNotExist:
                return None

        elif method == 'wordpress_site':
            try:
                custom_wp_openid_url = '%s?user_id=%s' % (wordpress_url, wp_user_id)
                assoc = UserAssociation.objects.get(
                                            openid_url = custom_wp_openid_url,
                                            provider_name = 'wordpress_site'
                                            )
                user = assoc.user
            except UserAssociation.DoesNotExist:
                return None
        elif method == 'force':
            return self.get_user(user_id)
        else:
            raise TypeError('only openid and password supported')

        #update last used time
        assoc.last_used_timestamp = datetime.datetime.now()
        assoc.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @classmethod
    def set_password(cls, 
                    user=None,
                    password=None,
                    provider_name=None
                ):
        """generic method to change password of
        any for any login provider that uses password
        and allows the password change function
        """
        login_providers = util.get_enabled_login_providers()
        if login_providers[provider_name]['type'] != 'password':
            raise ImproperlyConfigured('login provider must use password')

        if provider_name == 'local':
            user.set_password(password)
            user.save()
            scrambled_password = user.password + str(user.id)
        else:
            raise NotImplementedError('external passwords not supported')

        try:
            assoc = UserAssociation.objects.get(
                                        user = user,
                                        provider_name = provider_name
                                    )
        except UserAssociation.DoesNotExist:
            assoc = UserAssociation(
                        user = user,
                        provider_name = provider_name
                    )

        assoc.openid_url = scrambled_password
        assoc.last_used_timestamp = datetime.datetime.now()
        assoc.save()
