"""
Q&A website settings - title, desctiption, basic urls
keywords
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps import livesettings
from django.utils.translation import ugettext as _
from django.utils.html import escape
from askbot import const

QA_SITE_SETTINGS = livesettings.ConfigurationGroup(
                    'QA_SITE_SETTINGS',
                    _('Q&A forum website parameters and urls')
                )

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_TITLE',
        default=u'ASKBOT: Open Source Q&A Forum',
        description=_('Site title for the Q&A forum')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_KEYWORDS',
        default=u'ASKBOT,CNPROG,forum,community',
        description=_('Comma separated list of Q&A site keywords')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_COPYRIGHT',
        default='Copyright ASKBOT, 2010. Some rights reserved ' + \
                'under creative commons license.',
        description=_('Copyright message to show in the footer')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_DESCRIPTION',
        default='Open source question and answer forum written in ' +\
                'Python and Django',
        description=_('Site description for the search engines')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_SHORT_NAME',
        default='Askbot',
        description=_('Short name for your Q&A forum')
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'APP_URL',
        default='http://askbot.org',
        description=_(
                'Base URL for your Q&A forum, must start with '
                'http or https'
            ),
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'GREETING_URL',
        default='/' + _('faq/'),#cannot reverse url here, must be absolute also
        hidden=True,
        description=_(
                'Link shown in the greeting message '
                'shown to the anonymous user'
            ),
        help_text=_('If you change this url from the default - '
                    'then you will also probably want to adjust translation of '
                    'the following string: ') + '"' 
                    + escape(const.GREETING_FOR_ANONYMOUS_USER + '"'
                    ' You can find this string in your locale django.po file'
                    )
    )
)

settings.register(
    livesettings.StringValue(
        QA_SITE_SETTINGS,
        'FEEDBACK_SITE_URL',
        description=_('Feedback site URL'),
        help_text=_(
                'If left empty, a simple internal feedback form '
                'will be used instead'
            )
    )
)
