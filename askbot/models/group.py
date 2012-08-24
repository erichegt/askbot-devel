import re
from askbot.models.tag import Tag
from askbot.conf import settings as askbot_settings

def get_global_group():
    """Returns the global group,
    if necessary, creates one
    """
    #todo: when groups are disconnected from tags,
    #find comment as shown below in the test cases and
    #revert the values
    #todo: change groups to django groups
    group_name = askbot_settings.GLOBAL_GROUP_NAME
    try:
        return Tag.group_tags.get(name=group_name)
    except Tag.DoesNotExist:
        from askbot.models import get_admin
        return Tag.group_tags.get_or_create(
                            group_name=group_name,
                            user=get_admin(),
                            is_open=False
                        )

def get_groups():
    return Tag.group_tags.get_all()

def get_group_names():
    #todo: cache me
    return get_groups().values_list('name', flat = True)

def get_group_manager():
    #This will be the place to replace with the new model
    return Tag.group_tags

def clean_group_name(name):
    """group names allow spaces,
    tag names do not, so we use this method
    to replace spaces with dashes"""
    return re.sub('\s+', '-', name.strip())
