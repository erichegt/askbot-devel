"""
External service key settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps import livesettings
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings

EXTERNAL_KEYS = livesettings.ConfigurationGroup(
                    'EXTERNAL_KEYS',
                    _('Keys to connect the site with external services like Facebook, etc.')
                )

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'GOOGLE_SITEMAP_CODE',
        description=_('Google site verification key'),
        help_text=_(
                        'This key helps google index your site '
                        'please obtain is at '
                        '<a href="%(google_webmasters_tools_url)s">'
                        'google webmasters tools site</a>'
                    ) % {'google_webmasters_tools_url':
                        'https://www.google.com/webmasters/tools/home?hl=' \
                        + django_settings.LANGUAGE_CODE}
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'GOOGLE_ANALYTICS_KEY',
        description=_('Google Analytics key'),
        help_text=_(
                        'Obtain is at <a href="%(ga_site)s">'
                        'Google Analytics</a> site, if you '
                        'wish to use Google Analytics to monitor '
                        'your site'
                    ) % {'ga_site':'http://www.google.com/intl/%s/analytics/' \
                            % django_settings.LANGUAGE_CODE }
    )
)

settings.register(
    livesettings.BooleanValue(
        EXTERNAL_KEYS,
        'USE_RECAPTCHA',
        description=_('Enable recaptcha (keys below are required)'),
        default=False
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'RECAPTCHA_KEY',
        description=_('Recaptcha public key')
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'RECAPTCHA_SECRET',
        description=_('Recaptcha private key'),
        help_text=_(
                        'Recaptcha is a tool that helps distinguish '
                        'real people from annoying spam robots. '
                        'Please get this and a public key at '
                        'the <a href="http://recaptcha.net">recaptcha.net</a>'
                    )
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'FACEBOOK_KEY',
        description=_('Facebook public API key'),
        help_text=_(
                     'Facebook API key and Facebook secret '
                     'allow to use Facebook Connect login method '
                     'at your site. Please obtain these keys '
                     'at <a href="http://www.facebook.com/developers/createapp.php">'
                     'facebook create app</a> site'
                    )
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'FACEBOOK_SECRET',
        description=_('Facebook secret key')
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'TWITTER_KEY',
        description=_('Twitter consumer key'),
        help_text=_(
            'Please register your forum at <a href="http://dev.twitter.com/apps/">'
            'twitter applications site</a>'
        ),

    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'TWITTER_SECRET',
        description=_('Twitter consumer secret'),
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'LINKEDIN_KEY',
        description=_('LinkedIn consumer key'),
        help_text=_(
            'Please register your forum at <a href="http://dev.twitter.com/apps/">'
            'twitter applications site</a>'
        ),

    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'LINKEDIN_SECRET',
        description=_('LinkedIn consumer secret'),
    )
)

settings.register(
    livesettings.BooleanValue(
        EXTERNAL_KEYS,
        'USE_LDAP_FOR_PASSWORD_LOGIN',
        description=_('Use LDAP authentication for the password login'),
        defaut=False
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'LDAP_PROVIDER_NAME',
        description=_('LDAP service provider name')
    )
)

settings.register(
    livesettings.StringValue(
        EXTERNAL_KEYS,
        'LDAP_URL',
        description=_('URL for the LDAP service')
    )
)

settings.register(
    livesettings.LongStringValue(
        EXTERNAL_KEYS,
        'HOW_TO_CHANGE_LDAP_PASSWORD',
        description=_('Explain how to change LDAP password')
    )
)
