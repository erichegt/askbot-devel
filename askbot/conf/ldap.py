"""Settings for LDAP login for Askbot"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import EXTERNAL_SERVICES
from askbot.deps import livesettings
from django.utils.translation import ugettext as _

LDAP_SETTINGS = livesettings.ConfigurationGroup(
                    'LDAP_SETTINGS',
                    _('LDAP login configuration'),
                    super_group = EXTERNAL_SERVICES
                )

settings.register(
    livesettings.BooleanValue(
        LDAP_SETTINGS,
        'USE_LDAP_FOR_PASSWORD_LOGIN',
        description=_('Use LDAP authentication for the password login'),
        defaut=False
    )
)

LDAP_PROTOCOL_VERSION_CHOICES = (
    ('3', _('Version 3')),
    ('2', _('Version 2 (insecure and deprecated)!!!'))
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_PROTOCOL_VERSION',
        default = '3',
        choices = LDAP_PROTOCOL_VERSION_CHOICES,
        description = _('LDAP protocol version'),
        help_text = _(
            'Note that Version 2 protocol is not secure!!! '
            'Do not use it on unprotected network.'
        )
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_URL',
        description=_('LDAP URL'),
        default="ldap://<host>:<port>"
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_BASEDN',
        description=_('LDAP BASE DN')
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_USER_FILTER_TEMPLATE',
        description = _('User search filter template'),
        default = '(%s=%s)',
        help_text = _(
            'Python string format template, must have two string placeholders'
        )
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_SEARCH_SCOPE',
        description=_('LDAP Search Scope'),
        default="subs"
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_USERID_FIELD',
        description=_('LDAP Server USERID field name'),
        default="uid" 
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_COMMONNAME_FIELD',
        description=_('LDAP Server "Common Name" field name'),
        default="cn"
    )
)

settings.register(
    livesettings.StringValue(
        LDAP_SETTINGS,
        'LDAP_EMAIL_FIELD',
        description=_('LDAP Server EMAIL field name'),
        default="mail"
    )
)

# May be necessary, but not handled properly.
# --> Commenting out until handled properly in backends.ldap_authenticate()
#settings.register(
#    livesettings.StringValue(
#        LDAP_SETTINGS,
#        'LDAP_PROXYDN',
#        description=_('LDAP PROXY DN'),
#        default=""
#    )
#)
#
#settings.register(
#    livesettings.StringValue(
#        LDAP_SETTINGS,
#        'LDAP_PROXYDN_PASSWORD',
#        description=_('LDAP PROXY DN Password'),
#        defalut="",
#    )
#)
