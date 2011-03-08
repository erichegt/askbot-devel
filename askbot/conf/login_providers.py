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

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'PASSWORD_REGISTER_SHOW_PROVIDER_BUTTONS',
        default = False,
        description=_('Show login proviers on Sign Up'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'SIGNIN_ALWAYS_SHOW_LOCAL_LOGIN',
        default = True,
        description=_('Always display local login and hide Askbot button.'),
    )
)

providers = (('SIGNIN_TWITTER_ENABLED', 'Activate Twitter login'),
              ('SIGNIN_GOOGLE_ENABLED', 'Activate Google login'),
              ('SIGNIN_LINKEDIN_ENABLED', 'Activate LinkedIn login'),
              ('SIGNIN_YAHOO_ENABLED', 'Activate Yahoo! login'),
              ('SIGNIN_AOL_ENABLED', 'Activate AOL login'),
              ('SIGNIN_OPENID_ENABLED', 'Activate OpenID login'),
              ('SIGNIN_FACEBOOK_ENABLED', 'Activate Facebook login'),
              ('SIGNIN_LOCAL_ENABLED', 'Activate Local login'),
              ('SIGNIN_FLICKR_ENABLED', 'Activate Flickr login'),
              ('SIGNIN_TECHNORATI_ENABLED', 'Activate Technorati login'),
              ('SIGNIN_WORDPRESS_ENABLED', 'Activate Wordpress login'),
              ('SIGNIN_BLOGGER_ENABLED', 'Activate Blogger login'),
              ('SIGNIN_LIVEJOURNAL_ENABLED', 'Activate LiveJournal login'),
              ('SIGNIN_CLAIMID_ENABLED', 'Activate ClaimID login'),
              ('SIGNIN_VIDOOP_ENABLED', 'Activate Vidoop login'),
              ('SIGNIN_VERISIGN_ENABLED', 'Activate Verisign login')
            )
                  
for key, value in providers:
    settings.register(
        livesettings.BooleanValue(
            LOGIN_PROVIDERS,
            key,
            description=_(value),
            default = True
        )
    )
