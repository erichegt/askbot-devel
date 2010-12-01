"""
Settings for reputation changes that apply to 
user in response to various actions by the same
users or others
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue
from django.utils.translation import ugettext as _

REP_CHANGES = ConfigurationGroup(
                    'BADGES',
                    _('Badge settings'),
                    ordering=2
                )

settings.register(
    IntegerValue(
        REP_CHANGES,
        'DISCIPLINED_BADGE_MIN_UPVOTES',
        default=3,
        description=_('Disciplined: minimum upvotes for deleted post')
    )
)

settings.register(
    IntegerValue(
        REP_CHANGES,
        'PEER_PRESSURE_BADGE_MIN_DOWNVOTES',
        default=3,
        description=_('Peer Pressure: minimum downvotes for deleted post')
    )
)
