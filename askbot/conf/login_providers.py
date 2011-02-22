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
        'twitter',
        description=_('Activate Twitter')
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'google',
        description=_('Activate Google'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'linkedin',
        description=_('Activate LinkedIn'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'yahoo',
        description=_('Activate Yahoo'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'aol',
        description=_('Activate AOL'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'openid',
        description=_('Activate OpenID'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'facebook',
        description=_('Activate Facebook'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'local',
        description=_('Activate Local Login'),
    )
)
#Minor providers

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'flickr',
        description=_('Activate Flickr'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'technorati',
        description=_('Activate Technorati'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'wordpress',
        description=_('Activate Wordpress'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'blogger',
        description=_('Activate Blogger'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'livejournal',
        description=_('Activate LiveJournal'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'claimid',
        description=_('Activate Claimid'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'vidoop',
        description=_('Activate Vidoop'),
    )
)

settings.register(
    livesettings.BooleanValue(
        LOGIN_PROVIDERS,
        'verisign',
        description=_('Activate Verisign'),
    )
)
