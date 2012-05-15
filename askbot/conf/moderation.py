"""Settings to control content moderation"""

from askbot.conf.settings_wrapper import settings
from askbot.conf.super_groups import DATA_AND_FORMATTING
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import BooleanValue
from django.utils.translation import ugettext as _

MODERATION = ConfigurationGroup(
                    'MODERATION',
                    _('Content moderation'),
                    super_group = DATA_AND_FORMATTING
                )

settings.register(
    BooleanValue(
        MODERATION,
        'ENABLE_CONTENT_MODERATION',
        default = False,
        description = _('Enable content moderation'),
    )
)
