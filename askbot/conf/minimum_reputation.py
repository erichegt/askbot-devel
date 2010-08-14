"""
Settings for minimum reputation required for 
a variety of actions on the askbot askbot
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue
from django.utils.translation import ugettext as _

MIN_REP = ConfigurationGroup(
                    'MIN_REP', 
                    _('Minimum reputation required to perform actions'),
                    ordering=0
                )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_VOTE_UP',
                    default=15,
                    description=_('Upvote')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_VOTE_DOWN',
                    default=100,
                    description=_('Downvote')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_FLAG_OFFENSIVE',
                    default=15,
                    description=_('Flag offensive')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_LEAVE_COMMENTS',
                    default=50,
                    description=_('Leave comments')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_DELETE_OTHERS_COMMENTS',
                    default=2000,
                    description=_('Delete comments posted by others')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_DELETE_OTHERS_POSTS',
                    default=5000,
                    description=_('Delete questions and answers posted by others')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_UPLOAD_FILES',
                    default=60,
                    description=_('Upload files')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_CLOSE_OWN_QUESTIONS',
                    default=250,
                    description=_('Close own questions'),
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_RETAG_OTHERS_QUESTIONS',
                    default=500,
                    description=_('Retag questions posted by other people')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_REOPEN_OWN_QUESTIONS',
                    default=500,
                    description=_('Reopen own questions')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_EDIT_WIKI',
                    default=750,
                    description=_('Edit community wiki posts')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_EDIT_OTHERS_POSTS',
                    default=2000,
                    description=_('Edit posts authored by other people')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_VIEW_OFFENSIVE_FLAGS',
                    default=2000,
                    description=_('View offensive flags')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_CLOSE_OTHERS_QUESTIONS',
                    default=2000,
                    description=_('Close questions asked by others')
                )
            )

settings.register(
                IntegerValue(
                    MIN_REP,
                    'MIN_REP_TO_LOCK_POSTS',
                    default=4000,
                    description=_('Lock posts')
                )
            )
