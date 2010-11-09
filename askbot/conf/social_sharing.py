"""
Social sharing settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, BooleanValue
from django.utils.translation import ugettext as _

SOCIAL_SHARING = ConfigurationGroup(
            'SOCIAL_SHARING',
            _('Sharing content on social networks'), 
        )

settings.register(
    BooleanValue(
        SOCIAL_SHARING,
        'ENABLE_SOCIAL_SHARING',
        default=True,
        description=_('Check to enable sharing of questions on Twitter and Facebook')
    )
)
