"""
General skin settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import StringValue, IntegerValue, BooleanValue
from django.utils.translation import ugettext as _
from askbot.skins.utils import get_skin_choices

GENERAL_SKIN_SETTINGS = ConfigurationGroup(
                    'GENERAL_SKIN_SETTINGS',
                    _('Skin and User Interface settings'),
                )

settings.register(
    BooleanValue(
        GENERAL_SKIN_SETTINGS,
        'ALWAYS_SHOW_ALL_UI_FUNCTIONS',
        default = False,
        description = _('Show all UI functions to all users'),
        help_text = _(
                        'If checked, all forum functions '
                        'will be shown to users, regardless of their '
                        'reputation. However to use those functions, '
                        'moderation rules, reputation and other limits '
                        'will still apply.'
                    )
    )
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
