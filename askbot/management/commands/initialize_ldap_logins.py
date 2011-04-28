"""Management command to create LDAP login method for all users.
Please see description of the command in its ``help_text``.
"""
import datetime
from django.core.management.base import CommandError
from django.utils.translation import ugettext as _
from askbot.management import NoArgsJob
from askbot import models
from askbot.deps.django_authopenid.models import UserAssociation
from askbot.conf import settings as askbot_settings

def create_ldap_login_for_user(user):
    """a unit job that creates LDAP account record for
    the user, assuming that his or her LDAP user name
    is the same as the user name on the forum site.
    If the record already exists, LDAP provider name
    will be updated according to the live setting,
    otherwise a new record will be created.
    Always returns ``True``.
    """
    ldap_url = askbot_settings.LDAP_URL
    ldap_provider_name = askbot_settings.LDAP_PROVIDER_NAME
    if '' in (ldap_url, ldap_provider_name):
        raise CommandError(
                'Please, first set up LDAP settings '
                'at url /settings/EXTERNAL_KEYS,'
                'relative to the base url of your forum site'
            )
    try:
        assoc = UserAssociation.objects.get(
                    openid_url = user.username,
                    user = user
                )
    except UserAssociation.DoesNotExist:
        assoc = UserAssociation(
            openid_url = user.username,
            user = user
        )
    assoc.provider_name = ldap_provider_name
    assoc.last_used_timestamp = datetime.datetime.now()
    assoc.save()
    return True

class Command(NoArgsJob):
    """definition of the job that 
    runs through all users and creates LDAP login 
    methods, assuming that LDAP user ID's are the same 
    as values ``~askbot.User.username``
    """
    help = _(
        'This command may help you migrate to LDAP '
        'password authentication by creating a record '
        'for LDAP association with each user account. '
        'There is an assumption that ldap user id\'s are '
        'the same as user names registered at the site. '
        'Before running this command it is necessary to '
        'set up LDAP parameters in the "External keys" section '
        'of the site settings.'
    )
    def __init__(self, *args, **kwargs):
        self.batches = ({
            'title': 'Initializing LDAP logins for all users: ',
            'query_set': models.User.objects.all(),
            'function': create_ldap_login_for_user,
            'changed_count_message': 'Created LDAP logins for %d users',
            'nothing_changed_message': 'All users already have LDAP login methods'
        },)
        super(Command, self).__init__(*args, **kwargs)
