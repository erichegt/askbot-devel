"""
Q&A website settings - title, desctiption, basic urls
keywords
"""
from forum.conf.settings_wrapper import settings
from livesettings import ConfigurationGroup, StringValue
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings
from forum import const
from django.core.urlresolvers import reverse

QA_SITE_SETTINGS = ConfigurationGroup(
                    'QA_SITE_SETTINGS',
                    _('Q&A forum website parameters and urls')
                )

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'APP_TITLE',
        default=u'ASKBOT: Open Source Q&A Forum',
        description=_('Site title for the Q&A forum')
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'APP_KEYWORDS',
        default=u'ASKBOT,CNPROG,forum,community',
        description=_('Comma separated list of Q&A site keywords')
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'APP_COPYRIGHT',
        default='Copyright ASKBOT, 2010. Some rights reserved under creative commons license.',
        description=_('Copyright message to show in the footer')
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'APP_DESCRIPTION',
        default='Open source question and answer forum written in Python and Django',
        description=_('Site description for the search engines')
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'APP_URL',
        default='http://askbot.org',
        description=_('Base URL for your Q&A forum, must start with http or https'),
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'GREETING_URL',
        default=reverse('faq'),
        description=_('Link shown in the greeting message shown to the anonymous user'),
        help_text=_('If you change this url from the default - '
                    'then you wil have to adjust translation of '
                    'the following string: ') + const.GREETING_FOR_ANONYMOUS_USER
    )
)

settings.register(
    StringValue(
        QA_SITE_SETTINGS,
        'FEEBACK_SITE_URL'
        description=_('Feedback site URL'),
        help_text=_('If left empty, a simple internal feedback form will be used instead')
    )
)
