"""
Email related settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, IntegerValue, BooleanValue
from askbot.deps.livesettings import StringValue
from django.utils.translation import ugettext as _
from askbot import const

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
    StringValue(
        EMAIL,
        'DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE',
        default='w',
        choices=const.NOTIFICATION_DELIVERY_SCHEDULE_CHOICES,
        description=_('Default news notification frequency'),
        help_text=_(
                    'This option currently defines default frequency '
                    'of emailed updates in the following five categories: '
                    'questions asked by user, answered by user, individually '
                    'selected, entire forum (per person tag filter applies) '
                    'and posts mentioning the user and comment responses'
                    )
    )
)

settings.register(
    BooleanValue(
        EMAIL,
        'EMAIL_VALIDATION',
        default=False,
        hidden=True,
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

settings.register(
    StringValue(
        EMAIL,
        'EMAIL_SUBJECT_PREFIX',
        default='',
        description=_('Prefix for the email subject line'),
    )
)
