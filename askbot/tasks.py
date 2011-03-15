from django.contrib.contenttypes.models import ContentType
from celery.decorators import task
from askbot.models import Activity
from askbot.models import User
from askbot.models import send_instant_notifications_about_activity_in_post

@task(ignore_results = True)
def record_post_update_task(
        post_id,
        post_content_type_id,
        newly_mentioned_user_id_list = None, 
        updated_by_id = None,
        timestamp = None,
        created = False,
    ):

    updated_by = User.objects.get(id = updated_by_id)
    post_content_type = ContentType.objects.get(id = post_content_type_id)
    post = post_content_type.get_object_for_this_type(id = post_id)

    #todo: take into account created == True case
    (activity_type, update_object) = post.get_updated_activity_data(created)

    update_activity = Activity(
                    user = updated_by,
                    active_at = timestamp, 
                    content_object = post, 
                    activity_type = activity_type,
                    question = post.get_origin_post()
                )
    update_activity.save()

    #what users are included depends on the post type
    #for example for question - all Q&A contributors
    #are included, for comments only authors of comments and parent 
    #post are included
    recipients = post.get_response_receivers(
                                exclude_list = [updated_by, ]
                            )

    update_activity.add_recipients(recipients)

    assert(updated_by not in recipients)

    newly_mentioned_users = User.objects.filter(
                                id__in = newly_mentioned_user_id_list
                            )

    for user in set(recipients) | set(newly_mentioned_users):
        user.increment_response_count()
        user.save()

    #todo: weird thing is that only comments need the recipients
    #todo: debug these calls and then uncomment in the repo
    #argument to this call
    notification_subscribers = post.get_instant_notification_subscribers(
                                    potential_subscribers = recipients,
                                    mentioned_users = newly_mentioned_users,
                                    exclude_list = [updated_by, ]
                                )
    #todo: fix this temporary spam protection plug
    if created:
        if not (updated_by.is_administrator() or updated_by.is_moderator()):
            if updated_by.reputation < 15:
                notification_subscribers = \
                    [u for u in notification_subscribers if u.is_administrator()]
    send_instant_notifications_about_activity_in_post(
                            update_activity = update_activity,
                            post = post,
                            recipients = notification_subscribers,
                        )
