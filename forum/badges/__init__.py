import re

from forum.badges.base import BadgeImplementation
from forum.modules import get_modules_script_classes

ALL_BADGES = dict([
            (re.sub('BadgeImpl', '', name).lower(), cls) for name, cls
            in get_modules_script_classes('badges', BadgeImplementation).items()
            if not re.search('AbstractBadgeImpl$', name)
        ])