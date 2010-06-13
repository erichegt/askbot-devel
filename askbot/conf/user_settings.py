"""
User policy settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue, IntegerValue
from django.utils.translation import ugettext as _

USER_SETTINGS = ConfigurationGroup(
                    'USER_SETTINGS',
                    _('User policy settings')
                )

settings.register(
    BooleanValue(
        USER_SETTINGS,
        'EDITABLE_SCREEN_NAME',
        default=True,
        description=_('Allow editing user screen name')
    )
)

settings.register(
    IntegerValue(
        USER_SETTINGS,
        'MIN_USERNAME_LENGTH',
        hidden=True,
        default=1,
        description=_('Minimum allowed length for screen name')
    )
)
