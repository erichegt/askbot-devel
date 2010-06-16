"""
External service key settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup, StringValue
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings

EXTERNAL_KEYS = ConfigurationGroup(
                    'EXTERNAL_KEYS',
                    _('Keys to connect the site with external services like Facebook, etc.')
                )

settings.register(
    StringValue(
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
    StringValue(
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
    StringValue(
        EXTERNAL_KEYS,
        'RECAPTCHA_PRIVATE_KEY',
        description=_('Recaptcha private key') + ' - does not work yet',
        hidden=True,
        help_text=_(
                        'Recaptcha is a tool that helps distinguish '
                        'real people from annoying spam robots. '
                        'Please get this and a public key at '
                        'the <a href="http://recaptcha.net">recaptcha.net</a>'
                    )
    )
)

settings.register(
    StringValue(
        EXTERNAL_KEYS,
        'RECAPTCHA_PUBLIC_KEY',
        hidden=True,
        description=_('Recaptcha public key') + ' - does not work yet'
    )
)

settings.register(
    StringValue(
        EXTERNAL_KEYS,
        'FB_API_KEY',
        description=_('Facebook public API key') + ' - does not work yet',
        hidden=True,
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
    StringValue(
        EXTERNAL_KEYS,
        'FB_SECRET',
        hidden=True,
        description=_('Facebook secret key') + ' - does not work yet'
    )
)
