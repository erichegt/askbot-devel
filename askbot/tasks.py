"""Definitions of Celery tasks in Askbot
in this module there are two types of functions:

* those wrapped with a @task decorator and a ``_celery_task`` suffix - celery tasks
* those with the same base name, but without the decorator and the name suffix
  the actual work units run by the task

Celery tasks are special functions in a way that they require all the parameters
be serializable - so instead of ORM objects we pass object id's and
instead of query sets - lists of ORM object id's.

That is the reason for having two types of methods here:

* the base methods (those without the decorator and the
  ``_celery_task`` in the end of the name
  are work units that are called from the celery tasks.
* celery tasks - shells that reconstitute the necessary ORM
  objects and call the base methods
"""
import sys
import traceback
import logging
import uuid

from django.contrib.contenttypes.models import ContentType
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext as _
from celery.decorators import task
from askbot.conf import settings as askbot_settings
from askbot import const
from askbot import mail
from askbot.models import Post, Thread, User, ReplyAddress
from askbot.models.badges import award_badges_signal
from askbot.models import get_reply_to_addresses, format_instant_notification_email
from askbot import exceptions as askbot_exceptions

# TODO: Make exceptions raised inside record_post_update_celery_task() ...
#       ... propagate upwards to test runner, if only CELERY_ALWAYS_EAGER = True
#       (i.e. if Celery tasks are not deferred but executed straight away)

@task(ignore_result = True)
def notify_author_of_published_revision_celery_task(revision):
    #todo: move this to ``askbot.mail`` module
    #for answerable email only for now, because
    #we don't yet have the template for the read-only notification
    if askbot_settings.REPLY_BY_EMAIL:
        #generate two reply codes (one for edit and one for addition)
        #to format an answerable email or not answerable email
        reply_options = {
            'user': revision.author,
            'post': revision.post,
            'reply_action': 'append_content'
        }
        append_content_address = ReplyAddress.objects.create_new(
                                                        **reply_options
                                                    ).as_email_address()
        reply_options['reply_action'] = 'replace_content'
        replace_content_address = ReplyAddress.objects.create_new(
                                                        **reply_options
                                                    ).as_email_address()

        #populate template context variables
        reply_code = append_content_address + ',' + replace_content_address
        if revision.post.post_type == 'question':
            mailto_link_subject = revision.post.thread.title
        else:
            mailto_link_subject = _('An edit for my answer')
        #todo: possibly add more mailto thread headers to organize messages

        prompt = _('To add to your post EDIT ABOVE THIS LINE')
        reply_separator_line = const.SIMPLE_REPLY_SEPARATOR_TEMPLATE % prompt
        data = {
            'site_name': askbot_settings.APP_SHORT_NAME,
            'post': revision.post,
            'author_email_signature': revision.author.email_signature,
            'replace_content_address': replace_content_address,
            'reply_separator_line': reply_separator_line,
            'mailto_link_subject': mailto_link_subject,
            'reply_code': reply_code
        }

        #load the template
        template = get_template('email/notify_author_about_approved_post.html')
        #todo: possibly add headers to organize messages in threads
        headers = {'Reply-To': append_content_address}
        #send the message
        mail.send_mail(
            subject_line = _('Your post at %(site_name)s is now published') % data,
            body_text = template.render(Context(data)),
            recipient_list = [revision.author.email,],
            related_object = revision,
            activity_type = const.TYPE_ACTIVITY_EMAIL_UPDATE_SENT,
            headers = headers
        )

@task(ignore_result = True)
def record_post_update_celery_task(
        post_id,
        post_content_type_id,
        newly_mentioned_user_id_list = None,
        updated_by_id = None,
        timestamp = None,
        created = False,
        diff = None,
    ):
    #reconstitute objects from the database
    updated_by = User.objects.get(id=updated_by_id)
    post_content_type = ContentType.objects.get(id=post_content_type_id)
    post = post_content_type.get_object_for_this_type(id=post_id)
    newly_mentioned_users = User.objects.filter(
                                id__in=newly_mentioned_user_id_list
                            )
    try:
        notify_sets = post.get_notify_sets(
                                mentioned_users=newly_mentioned_users,
                                exclude_list=[updated_by,]
                            )
        #todo: take into account created == True case
        #update_object is not used
        (activity_type, update_object) = post.get_updated_activity_data(created)

        post.issue_update_notifications(
            updated_by=updated_by,
            notify_sets=notify_sets,
            activity_type=activity_type,
            timestamp=timestamp,
            diff=diff
        )

    except Exception:
        # HACK: exceptions from Celery job don't propagate upwards
        # to the Django test runner
        # so at least let's print tracebacks
        print >>sys.stderr, traceback.format_exc()
        raise

@task(ignore_result = True)
def record_question_visit(
    question_post = None,
    user_id = None,
    update_view_count = False):
    """celery task which records question visit by a person
    updates view counter, if necessary,
    and awards the badges associated with the
    question visit
    """
    #1) maybe update the view count
    #question_post = Post.objects.filter(
    #    id = question_post_id
    #).select_related('thread')[0]
    if update_view_count:
        question_post.thread.increase_view_count()

    user = User.objects.get(id=user_id)

    if user.is_anonymous():
        return

    #2) question view count per user and clear response displays
    #user = User.objects.get(id = user_id)
    if user.is_authenticated():
        #get response notifications
        user.visit_question(question_post)

    #3) send award badges signal for any badges
    #that are awarded for question views
    award_badges_signal.send(None,
                    event = 'view_question',
                    actor = user,
                    context_object = question_post,
                )

@task()
def send_instant_notifications_about_activity_in_post(
                                                update_activity = None,
                                                post = None,
                                                recipients = None,
                                            ):
    #reload object from the database
    post = Post.objects.get(id=post.id)
    if post.is_approved() is False:
        return

    if recipients is None:
        return

    acceptable_types = const.RESPONSE_ACTIVITY_TYPES_FOR_INSTANT_NOTIFICATIONS

    if update_activity.activity_type not in acceptable_types:
        return

    #calculate some variables used in the loop below
    update_type_map = const.RESPONSE_ACTIVITY_TYPE_MAP_FOR_TEMPLATES
    update_type = update_type_map[update_activity.activity_type]
    origin_post = post.get_origin_post()
    headers = mail.thread_headers(
                            post,
                            origin_post,
                            update_activity.activity_type
                        )

    logger = logging.getLogger()
    if logger.getEffectiveLevel() <= logging.DEBUG:
        log_id = uuid.uuid1()
        message = 'email-alert %s, logId=%s' % (post.get_absolute_url(), log_id)
        logger.debug(message)
    else:
        log_id = None


    for user in recipients:
        if user.is_blocked():
            continue

        reply_address, alt_reply_address = get_reply_to_addresses(user, post)

        subject_line, body_text = format_instant_notification_email(
                            to_user = user,
                            from_user = update_activity.user,
                            post = post,
                            reply_address = reply_address,
                            alt_reply_address = alt_reply_address,
                            update_type = update_type,
                            template = get_template('email/instant_notification.html')
                        )

        headers['Reply-To'] = reply_address
        try:
            mail.send_mail(
                subject_line=subject_line,
                body_text=body_text,
                recipient_list=[user.email],
                related_object=origin_post,
                activity_type=const.TYPE_ACTIVITY_EMAIL_UPDATE_SENT,
                headers=headers,
                raise_on_failure=True
            )
        except askbot_exceptions.EmailNotSent, error:
            logger.debug(
                '%s, error=%s, logId=%s' % (user.email, error, log_id)
            )
        else:
            logger.debug('success %s, logId=%s' % (user.email, log_id))
