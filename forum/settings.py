#todo: this file is currently not in use
import os
from forum.deps.livesettings import ConfigurationGroup, IntegerValue, config_register

INSTALLED_APPS = ['forum']

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'forum.middleware.anon_user.ConnectToSessionMessagesMiddleware',
    'forum.middleware.pagesize.QuestionsPageSizeMiddleware',
    'forum.middleware.cancel.CancelActionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
]

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'forum.modules.module_templates_loader',
    'forum.skins.load_template_source',
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.request',
    'forum.context.application_settings',
    'forum.user_messages.context_processors.user_messages',
    'django.core.context_processors.auth',
]

TEMPLATE_DIRS = [
    os.path.join(os.path.dirname(__file__),'skins').replace('\\','/'),
]

def setup_django_settings(settings):

    if (hasattr(settings, 'DEBUG') and getattr(settings, 'DEBUG')):
        try:
            import debug_toolbar
            INSTALLED_APPS.append('debug_toolbar')
            MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        except:
            pass


    settings.INSTALLED_APPS = set(settings.INSTALLED_APPS) | set(INSTALLED_APPS)
    settings.MIDDLEWARE_CLASSES = set(settings.MIDDLEWARE_CLASSES) | set(MIDDLEWARE_CLASSES)
    settings.TEMPLATE_LOADERS = set(settings.TEMPLATE_LOADERS) | set(TEMPLATE_LOADERS)
    settings.TEMPLATE_CONTEXT_PROCESSORS = set(settings.TEMPLATE_CONTEXT_PROCESSORS) | set(TEMPLATE_CONTEXT_PROCESSORS)
    settings.TEMPLATE_DIRS = set(settings.TEMPLATE_DIRS) | set(TEMPLATE_DIRS)


class AskbotConfigGroup(ConfigurationGroup):
    def __init__(self, key, name, *arg, **kwarg):
        super(AskbotConfigGroup, self).__init__(key, name, *arg,**kwarg)
        self.item_count = 0
    def new_int_setting(self, key, value, description):
        self.item_count += 1
        setting = config_register(IntegerValue(
                                        self,
                                        key,
                                        default=value,
                                        description=description,
                                        ordering=self.item_count
                                        )
                                )
        return setting
