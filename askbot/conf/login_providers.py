"""
External service key settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps import livesettings
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings

LOGIN_PROVIDERS = livesettings.ConfigurationGroup(
                    'LOGIN_PROVIDERS',
                    _('External login providers configuration.')
                )

providers = (('TWITTER', 'Activate Twitter'),
              ('GOOGLE', 'Activate Google'),
              ('LINKEDIN', 'Activate LinkedIn'),
              ('YAHOO', 'Activate Yahoo!'),
              ('AOL', 'Activate AOL'),
              ('OPENID', 'Activate OpenID'),
              ('FACEBOOK', 'Activate Facebook'),
              ('LOCAL', 'Activate Local login'),
              ('FLICKR', 'Activate Flickr'),
              ('TECHNORATI', 'Activate Technorati'),
              ('WORDPRESS', 'Activate Wordpress'),
              ('BLOGGER', 'Activate Blogger'),
              ('LIVEJOURNAL', 'Activate LiveJournal'),
              ('CLAIMID', 'Activate ClaimID'),
              ('VIDOOP', 'Activate Vidoop'),
              ('VERISIGN', 'Activate Verisign')
            )
                  
for key, value in providers:
    settings.register(
        livesettings.BooleanValue(
            LOGIN_PROVIDERS,
            key,
            description=_(value),
        )
    )

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'DISPLAYLOCAL',
        description=_('Always display local login and hide Askbot button.'),
    )
)
