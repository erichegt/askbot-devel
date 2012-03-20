"""Group settings"""
from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import LOGIN_USERS_COMMUNICATION
from askbot.deps import livesettings
from django.utils.translation import ugettext as _

GROUP_SETTINGS = livesettings.ConfigurationGroup(
                    'GROUP_SETTINGS',
                    _('Group settings'),
                    super_group = LOGIN_USERS_COMMUNICATION
                )

settings.register(
    livesettings.BooleanValue(
        GROUP_SETTINGS,
        'GROUPS_ENABLED',
        default = False,
        description = _('Enable user groups'),
    )
)
