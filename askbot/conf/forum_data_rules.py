"""
Settings for askbot data display and entry
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue, IntegerValue
from askbot.deps.livesettings import StringValue
from django.utils.translation import ugettext as _
from askbot import const

FORUM_DATA_RULES = ConfigurationGroup(
                        'FORUM_DATA_RULES',
                        _('Settings for askbot data entry and display')
                    )

settings.register(
    BooleanValue(
        FORUM_DATA_RULES,
        'WIKI_ON',
        default=True,
        description=_('Check to enable community wiki feature')
    )
)

settings.register(
    IntegerValue(
        FORUM_DATA_RULES,
        'MAX_TAG_LENGTH',
        default=20,
        description=_('Maximum length of tag (number of characters)')
    )
)

settings.register(
    IntegerValue(
        FORUM_DATA_RULES,
        'MAX_TAGS_PER_POST',
        default=5,
        description=_('Maximum number of tags per question')
    )
)

#todo: looks like there is a bug in askbot.deps.livesettings 
#that does not allow Integer values with defaults and choices
settings.register(
    StringValue(
        FORUM_DATA_RULES,
        'DEFAULT_QUESTIONS_PAGE_SIZE',
        choices=const.PAGE_SIZE_CHOICES,
        default='30',
        description=_('Number of questions to list by default')
    )
)

settings.register(
    StringValue(
        FORUM_DATA_RULES,
        'UNANSWERED_QUESTION_MEANING',
        choices=const.UNANSWERED_QUESTION_MEANING_CHOICES,
        default='NO_ACCEPTED_ANSWERS',
        description=_('What should "unanswered question" mean?')
    )
)
