import os
import pystache
from path_utils import SOURCE_DIR


class SettingsTemplate(pystache.View):
    '''Class for settings'''

    template_path = os.path.join(SOURCE_DIR, 'setup_templates')
    template_name = "settings.py"

    def __init__(self, context, **kwargs):
        super(SettingsTemplate, self).__init__(context=context, **kwargs)
