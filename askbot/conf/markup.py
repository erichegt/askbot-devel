"""
Settings that modify processing of user text input
"""

from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import BooleanValue, StringValue
from django.utils.translation import ugettext as _
import askbot
from askbot import const
import os

MARKUP = ConfigurationGroup(
                    'MARKUP',
                    _('Markup formatting')
                )

settings.register(
    BooleanValue(
        MARKUP,
        'MARKUP_CODE_FRIENDLY',
        description = _('Enable code-friendly Markdown'),
        help_text = _(
            'If checked, underscore characters will not '
            'trigger italic or bold formatting - '
            'bold and italic text can still be marked up '
            'with asterisks. Note that "MathJax support" '
            'implicitly turns this feature on, because '
            'underscores are heavily used in LaTeX input.'
        ),
        default = False
    )
)

settings.register(
    BooleanValue(
        MARKUP,
        'ENABLE_MATHJAX',
        description=_('Mathjax support (rendering of LaTeX)'),
        help_text=_(
                    'If you enable this feature, '
                    '<a href="%(url)s">mathjax</a> must be '
                    'installed on your server in its own directory.'
                    ) % {
                            'url': const.DEPENDENCY_URLS['mathjax'],
                        },
        default = False
    )
)

settings.register(
    StringValue(
        MARKUP,
        'MATHJAX_BASE_URL',
        description=_('Base url of MathJax deployment'),
        help_text=_(
                    'Note - <strong>MathJax is not included with '
                    'askbot</strong> - you should deploy it yourself, '
                    'preferably at a separate domain and enter url '
                    'pointing to the "mathjax" directory '
                    '(for example: http://mysite.com/mathjax)'
                    ),
        default = ''
    )
)
