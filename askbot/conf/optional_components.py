"""
External service key settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import BooleanValue, StringValue
from django.utils.translation import ugettext as _
import askbot
from askbot import const
import os

OPTIONAL_COMPONENTS = ConfigurationGroup(
                    'OPTIONAL_COMPONENTS',
                    _('Optional components')
                )

mathjax_dir = os.path.join(
                        askbot.get_install_directory(),
                        'skins',
                        'common',
                        'media'
                    )

settings.register(
    BooleanValue(
        OPTIONAL_COMPONENTS,
        'ENABLE_MATHJAX',
        description=_('Mathjax support (rendering of LaTeX)'),
        help_text=_(
                    'If you enable this feature, '
                    '<a href="%(url)s">mathjax</a> must be '
                    'installed in directory %(dir)s'
                    ) % {
                            'url': const.DEPENDENCY_URLS['mathjax'],
                            'dir': mathjax_dir,
                        },
        default = False
    )
)

settings.register(
    StringValue(
        OPTIONAL_COMPONENTS,
        'MATHJAX_BASE_URL',
        description=_('Base url of MathJax deployment'),
        help_text=_(
                    'Note - MathJax is not included with '
                    'askbot - you should deploy it yourself '
                    'and enter url pointing to the "mathjax" directory '
                    '(for example: http://mysite.com/mathjax'
                    ),
        default = ''
    )
)
