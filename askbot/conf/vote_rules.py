"""
Forum configuration settings detailing rules on votes
and offensive flags.

For example number of times a person can vote each day, etc.
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue
from django.utils.translation import ugettext as _

VOTE_RULES = ConfigurationGroup(
                    'VOTE_RULES', 
                    _('Limits applicable to votes and moderation flags'), 
                    ordering=1,
                )

settings.register(
    IntegerValue(
        VOTE_RULES,
        'MAX_VOTES_PER_USER_PER_DAY',
        default=30,
        description=_('Number of votes a user can cast per day')
    )
)

settings.register(
    IntegerValue(
        VOTE_RULES,
        'MAX_FLAGS_PER_USER_PER_DAY',
        default=5,
        description=_('Maximum number of flags per user per day')
    )
)

settings.register(
    IntegerValue(
        VOTE_RULES,
        'VOTES_LEFT_WARNING_THRESHOLD',
        default=5,
        description=_('Threshold for warning about remaining daily votes')
    )
)

settings.register(
    IntegerValue(
        VOTE_RULES,
        'MAX_DAYS_TO_CANCEL_VOTE',
        default=1,
        description=_('Number of days to allow canceling votes')
    )
)

settings.register(
    IntegerValue(
        VOTE_RULES,
        'MIN_FLAGS_TO_HIDE_POST',
        default=3,
        description=_('Number of flags required to automatically hide posts')
    )
)

settings.register(
    IntegerValue(
        VOTE_RULES,
        'MIN_FLAGS_TO_DELETE_POST',
        default=5,
        description=_('Number of flags required to automatically delete posts')
    )
)
