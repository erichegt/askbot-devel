"""
Site modes settings:
    Support for site modes currently supports
    Bootstrap - for sites that are starting and
    Default - for sites that already have a momentum.
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue
from django.utils.translation import ugettext as _
from askbot.conf import badges, minimum_reputation

def bootstrap_callback(current_value, new_value):
    '''Callback to update settings'''

    if current_value == new_value:
        #do not overwrite settings in case that tha value 
        #is the same
        return new_value

    if new_value == True:
        #minimum reputation settgins.
        settings.update('MIN_REP_TO_VOTE_UP', 5)
        settings.update('MIN_REP_TO_VOTE_DOWN', 50)
        settings.update('MIN_REP_TO_ANSWER_OWN_QUESTION', 5)
        settings.update('MIN_REP_TO_ACCEPT_OWN_ANSWER', 20)
        settings.update('MIN_REP_TO_FLAG_OFFENSIVE', 5)
        settings.update('MIN_REP_TO_LEAVE_COMMENTS', 10)
        settings.update('MIN_REP_TO_DELETE_OTHERS_COMMENTS', 200)
        settings.update('MIN_REP_TO_DELETE_OTHERS_POSTS', 500)
        settings.update('MIN_REP_TO_UPLOAD_FILES', 10)
        settings.update('MIN_REP_TO_CLOSE_OWN_QUESTIONS', 25)
        settings.update('MIN_REP_TO_RETAG_OTHERS_QUESTIONS', 50)
        settings.update('MIN_REP_TO_REOPEN_OWN_QUESTIONS', 50)
        settings.update('MIN_REP_TO_EDIT_WIKI', 75)
        settings.update('MIN_REP_TO_EDIT_OTHERS_POSTS', 200)
        settings.update('MIN_REP_TO_VIEW_OFFENSIVE_FLAGS', 200)
        settings.update('MIN_REP_TO_CLOSE_OTHERS_QUESTIONS', 200)
        settings.update('MIN_REP_TO_LOCK_POSTS', 400)
        settings.update('MIN_REP_TO_HAVE_STRONG_URL', 25)
        #badge settings
        settings.update('NOTABLE_QUESTION_BADGE_MIN_VIEWS', 25)
        settings.update('POPULAR_QUESTION_BADGE_MIN_VIEWS', 15)
        settings.update('FAMOUS_QUESTION_BADGE_MIN_VIEWS', 50)
        settings.update('ENTHUSIAST_BADGE_MIN_DAYS', 5)
        settings.update('TAXONOMIST_BADGE_MIN_USE_COUNT', 5)
    else:
        for key in badges.BADGES.keys():
            default_value = badges.BADGES[key].default
            settings.update(key, default_value)

        for key in minimum_reputation.MIN_REP.keys():
            default_value = minimum_reputation.MIN_REP[key].default
            settings.update(key, default_value)

    return new_value


SITE_MODES = ConfigurationGroup(
                    'SITE_MODES',
                    _('Reputation & limits mode'),
                )

settings.register(
    BooleanValue(
        SITE_MODES,
        'ACTIVATE_BOOTSTRAP_MODE',
        default=False,
        description=_('Check this value to activate a special "Bootstrap" mode'),
        help_text=_("<strong>WARNING:</strong> your current value for Minimum reputation and Bagde Settings will be changed after you save.."),
        update_callback = bootstrap_callback
    )
)
