"""
Email related settings
"""
from forum.conf.settings_wrapper import settings
from livesettings import ConfigurationGroup, IntegerValue, BooleanValue
from livesettings import StringValue
from django.utils.translation import ugettext as _

EMAIL = ConfigurationGroup(
            'EMAIL',
            _('Email and email alert settings'), 
        )

settings.register(
    IntegerValue(
        EMAIL,
        'MAX_ALERTS_PER_EMAIL',
        default=7,
        description=_('Maximum number of news entries in an email alert')
    )
)

settings.register(
    BooleanValue(
        EMAIL,
        'EMAIL_VALIDATION',
        default=False,
        description=_('Require email verification before allowing to post'),
        help_text=_('Active email verification is done by sending a verification key in email')
    )
)

settings.register(
    BooleanValue(
        EMAIL,
        'EMAIL_UNIQUE',
        default=True,
        description=_('Allow only one account per email address')
    )
)

settings.register(
    StringValue(
        EMAIL,
        'ANONYMOUS_USER_EMAIL',
        default='anonymous@askbot.org',
        description=_('Fake email for anonymous user'),
        help_text=_('Use this setting to control gravatar for email-less user')
    )
)
