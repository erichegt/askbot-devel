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

providers = (('SIGNIN_TWITTER_ENABLED', 'Activate Twitter'),
              ('SIGNIN_GOOGLE_ENABLED', 'Activate Google'),
              ('SIGNIN_LINKEDIN_ENABLED', 'Activate LinkedIn'),
              ('SIGNIN_YAHOO_ENABLED', 'Activate Yahoo!'),
              ('SIGNIN_AOL_ENABLED', 'Activate AOL'),
              ('SIGNIN_OPENID_ENABLED', 'Activate OpenID'),
              ('SIGNIN_FACEBOOK_ENABLED', 'Activate Facebook'),
              ('SIGNIN_LOCAL_ENABLED', 'Activate Local login'),
              ('SIGNIN_FLICKR_ENABLED', 'Activate Flickr'),
              ('SIGNIN_TECHNORATI_ENABLED', 'Activate Technorati'),
              ('SIGNIN_WORDPRESS_ENABLED', 'Activate Wordpress'),
              ('SIGNIN_BLOGGER_ENABLED', 'Activate Blogger'),
              ('SIGNIN_LIVEJOURNAL_ENABLED', 'Activate LiveJournal'),
              ('SIGNIN_CLAIMID_ENABLED', 'Activate ClaimID'),
              ('SIGNIN_VIDOOP_ENABLED', 'Activate Vidoop'),
              ('SIGNIN_VERISIGN_ENABLED', 'Activate Verisign')
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
