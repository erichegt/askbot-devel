"""place for the API calls into askbot
at this point most of the useful functions are still
in the askbot.models module, but
api must become a place to manupulate the data in the askbot application
so that other implementations of the data storage could be possible
"""
from askbot import models
from askbot import const

def get_info_on_moderation_items(user):
    """returns a dictionary with 
    counts of new and seen moderation items for a given user
    if user is not a moderator or admin, returns None
    """
    if user.is_anonymous():
        return None
    if not(user.is_moderator() or user.is_administrator()):
        return None

    messages = models.ActivityAuditStatus.objects.filter(
        activity__activity_type = const.TYPE_ACTIVITY_MARK_OFFENSIVE,
        user = user
    )

    seen_count = messages.filter(
                    status = models.ActivityAuditStatus.STATUS_SEEN
                ).count()
    new_count = messages.filter(
                    status = models.ActivityAuditStatus.STATUS_NEW
                ).count()
    return {
        'seen_count': seen_count,
        'new_count': new_count
    }
