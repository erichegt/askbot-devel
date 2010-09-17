"""
General skin settings
"""
from askbot.conf.settings_wrapper import settings
from askbot.deps.livesettings import ConfigurationGroup
from askbot.deps.livesettings import StringValue, IntegerValue, BooleanValue
from askbot.deps.livesettings import ImageValue
from django.utils.translation import ugettext as _
from django.conf import settings as django_settings
from askbot.skins import utils as skin_utils
from askbot import const

GENERAL_SKIN_SETTINGS = ConfigurationGroup(
                    'GENERAL_SKIN_SETTINGS',
                    _('Skin and User Interface settings'),
                )

settings.register(
    ImageValue(
        GENERAL_SKIN_SETTINGS,
        'SITE_LOGO_URL',
        description = _('Q&A site logo'),
        help_text = _(
                        'To change the logo, select new file, '
                        'then submit this whole form.'
                    ),
        upload_directory = django_settings.ASKBOT_FILE_UPLOAD_DIR,
        upload_url = '/' + django_settings.ASKBOT_UPLOADED_FILES_URL,
        default = '/images/logo.gif',
        url_resolver = skin_utils.get_media_url
    )
)

settings.register(
    ImageValue(
        GENERAL_SKIN_SETTINGS,
        'SITE_FAVICON',
        description = _('Site favicon'),
        help_text = _(
                        'A small 16x16 or 32x32 pixel icon image '
                        'used to distinguish your site in the browser '
                        'user interface. Please find more information about favicon '
                        'at <a href="%(favicon_info_url)s">this page</a>.'
                    ) % {'favicon_info_url': const.DEPENDENCY_URLS['favicon']},
        upload_directory = django_settings.ASKBOT_FILE_UPLOAD_DIR,
        upload_url = '/' + django_settings.ASKBOT_UPLOADED_FILES_URL,
        default = '/images/favicon.gif',
        url_resolver = skin_utils.get_media_url
    )
)

settings.register(
    ImageValue(
        GENERAL_SKIN_SETTINGS,
        'LOCAL_LOGIN_ICON',
        description = _('Password login button'),
        help_text = _(
                        'An 88x38 pixel image that is used on the login screen '
                        'for the password login button.'
                    ),
        upload_directory = django_settings.ASKBOT_FILE_UPLOAD_DIR,
        upload_url = '/' + django_settings.ASKBOT_UPLOADED_FILES_URL,
        default = '/images/pw-login.gif',
        url_resolver = skin_utils.get_media_url
    )
)

settings.register(
    BooleanValue(
        GENERAL_SKIN_SETTINGS,
        'ALWAYS_SHOW_ALL_UI_FUNCTIONS',
        default = False,
        description = _('Show all UI functions to all users'),
        help_text = _(
                        'If checked, all forum functions '
                        'will be shown to users, regardless of their '
                        'reputation. However to use those functions, '
                        'moderation rules, reputation and other limits '
                        'will still apply.'
                    )
    )
)

settings.register(
    StringValue(
        GENERAL_SKIN_SETTINGS,
        'ASKBOT_DEFAULT_SKIN',
        default = 'default',
        choices = skin_utils.get_skin_choices(),
        description = _('Select skin'),
    )
)

settings.register(
    IntegerValue(
        GENERAL_SKIN_SETTINGS,
        'MEDIA_RESOURCE_REVISION',
        default = 1,
        description = _('Skin media revision number'),
        help_text = _(
                    'Increment this number when you change '
                    'image in skin media or stylesheet. '
                    'This helps avoid showing your users '
                    'outdated images from their browser cache.'
                    )
    )
)
