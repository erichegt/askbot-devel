"""functions, preparing parts of context for
the templates in the various views"""
from django.utils import simplejson
from django.utils.translation import ugettext as _
from askbot.conf import settings as askbot_settings
from askbot import const
from askbot.const import message_keys as msg

def get_for_tag_editor():
    #data for the tag editor
    data = {
        'tag_regex': const.TAG_REGEX,
        'tags_are_required': askbot_settings.TAGS_ARE_REQUIRED,
        'max_tags_per_post': askbot_settings.MAX_TAGS_PER_POST,
        'max_tag_length': askbot_settings.MAX_TAG_LENGTH,
        'force_lowercase_tags': askbot_settings.FORCE_LOWERCASE_TAGS,
        'messages': {
            'required': _(msg.TAGS_ARE_REQUIRED_MESSAGE),
            'wrong_chars': _(msg.TAG_WRONG_CHARS_MESSAGE)
        }
    }
    return {'tag_editor_settings': simplejson.dumps(data)}
