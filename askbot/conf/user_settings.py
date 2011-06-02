"""
User policy settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps import livesettings
from django.utils.translation import ugettext as _

USER_SETTINGS = livesettings.ConfigurationGroup(
                    'USER_SETTINGS',
                    _('User policy settings')
                )

settings.register(
    livesettings.BooleanValue(
        USER_SETTINGS,
        'EDITABLE_SCREEN_NAME',
        default = True,
        description = _('Allow editing user screen name')
    )
)

settings.register(
    livesettings.BooleanValue(
        USER_SETTINGS,
        'ALLOW_ACCOUNT_RECOVERY_BY_EMAIL',
        default = True,
        description = _('Allow account recovery by email')
    )
)

settings.register(
    livesettings.BooleanValue(
        USER_SETTINGS,
        'ALLOW_ADD_REMOVE_LOGIN_METHODS',
        default = True,
        description = _('Allow adding and removing login methods')
    )
)

settings.register(
    livesettings.IntegerValue(
        USER_SETTINGS,
        'MIN_USERNAME_LENGTH',
        hidden=True,
        default=1,
        description=_('Minimum allowed length for screen name')
    )
)

settings.register(
    livesettings.StringValue(
        USER_SETTINGS,
        'NAME_OF_ANONYMOUS_USER',
        default = '',
        description = _('Name for the Anonymous user')
    )
)
