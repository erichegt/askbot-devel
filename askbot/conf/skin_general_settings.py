"""
General skin settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, StringValue, IntegerValue
from django.utils.translation import ugettext as _
from askbot.skins.utils import get_skin_choices

GENERAL_SKIN_SETTINGS = ConfigurationGroup(
                    'GENERAL_SKIN_SETTINGS',
                    _('Skin: general settings'),
                )

settings.register(
    StringValue(
        GENERAL_SKIN_SETTINGS,
        'ASKBOT_DEFAULT_SKIN',
        default='default',
        choices=get_skin_choices(),
        description=_('Select skin'),
    )
)

settings.register(
    IntegerValue(
        GENERAL_SKIN_SETTINGS,
        'MEDIA_RESOURCE_REVISION',
        default=1,
        description=_('Skin media revision number'),
        help_text=_(
                    'Increment this number when you change '
                    'image in skin media or stylesheet. '
                    'This helps avoid showing your users '
                    'outdated images from their browser cache.'
                    )
    )
)

