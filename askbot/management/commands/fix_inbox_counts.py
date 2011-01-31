from askbot.management import NoArgsJob
from askbot import models
from askbot import const

ACTIVITY_TYPES = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
ACTIVITY_TYPES += (const.TYPE_ACTIVITY_MENTION,)

def fix_inbox_counts(user):
    old_new_count = user.new_response_count
    old_seen_count = user.seen_response_count
    new_new_count = models.ActivityAuditStatus.objects.filter(
                            user = user,
                            status = models.ActivityAuditStatus.STATUS_NEW,
                            activity__activity_type__in = ACTIVITY_TYPES
                        ).count()
    new_seen_count = models.ActivityAuditStatus.objects.filter(
                            user = user,
                            status = models.ActivityAuditStatus.STATUS_SEEN,
                            activity__activity_type__in = ACTIVITY_TYPES
                        ).count()

    (changed1, changed2) = (False, False)
    if new_new_count != old_new_count:
        user.new_response_count = new_new_count
        changed1 = True
    if new_seen_count != old_seen_count:
        user.seen_response_count = new_seen_count
        changed2 = True
    if changed1 or changed2:
        user.save()
        return True
    return False

class Command(NoArgsJob):
    """definition of the job that fixes response counts
    destined for the user inboxes
    """
    def __init__(self, *args, **kwargs):
        self.batches = ({
            'title': 'Checking inbox item counts for all users: ',
            'query_set': models.User.objects.all(),
            'function': fix_inbox_counts,
            'changed_count_message': 'Corrected records for %d users',
            'nothing_changed_message': 'No problems found'
        },)
        super(Command, self).__init__(*args, **kwargs)
