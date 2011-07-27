"""
Sidebar settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import values
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings
from askbot.skins import utils as skin_utils
from askbot import const

SIDEBAR_SETTINGS = ConfigurationGroup(
                    'SIDEBAR_SETTINGS',
                    _('Sidebar Widget settings'),
                )

settings.register(
    values.BooleanValue(
        SIDEBAR_SETTINGS,
        'SIDEBAR_SHOW_AVATARS',
        description = _('Show avatar block in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the avatar '
                    'block from the sidebar ' 
                    ),
        default = True
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_SETTINGS,
        'SIDEBAR_SHOW_TAG_SELECTOR',
        description = _('Show tag selector in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the options '
                    'for choosing interesting and ignored tags ' 
                    ),
        default = True
    )
)

settings.register(
    values.BooleanValue(
        SIDEBAR_SETTINGS,
        'SIDEBAR_SHOW_TAGS',
        description = _('Show tag list/cloud in sidebar'),
        help_text = _(
                    'Uncheck this if you want to hide the tag '
                    'cloud or tag list from the sidebar ' 
                    ),
        default = True
    )
)

