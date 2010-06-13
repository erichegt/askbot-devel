"""
Q&A askbot flatpages (about, etc.)
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, LongStringValue
from django.utils.translation import ugettext as _

FLATPAGES = ConfigurationGroup(
                'FLATPAGES',
                _('Flatpages - about, privacy policy, etc.')
            )

settings.register(
    LongStringValue(
        FLATPAGES,
        'FORUM_ABOUT',
        description=_('Text the Q&A askbot About page (html format)'),
        help_text=\
        _(
            'Save, then <a href="http://validator.w3.org/">'
            'use HTML validator</a> on the "about" page to check your input.'
        )
    )
)

settings.register(
    LongStringValue(
        FLATPAGES,
        'FORUM_PRIVACY',
        description=_('Text the Q&A askbot Privacy Policy (html format)'),
        help_text=\
        _(
            'Save, then <a href="http://validator.w3.org/">'
            'use HTML validator</a> on the "privacy" page to check your input.'
        )
    )
)
