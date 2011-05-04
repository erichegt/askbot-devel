import datetime
from django.core.management.base import NoArgsCommand
from django.conf import settings as django_settings
from askbot import models
from askbot import const
from askbot.conf import settings as askbot_settings
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from askbot.utils import mail
from askbot.models.question import get_tag_summary_from_questions

DEBUG_THIS_COMMAND = False

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        if askbot_settings.ENABLE_UNANSWERED_REMINDERS == False:
            return
        #get questions without answers, excluding closed and deleted
        #order it by descending added_at date
        wait_period = datetime.timedelta(
            askbot_settings.DAYS_BEFORE_SENDING_UNANSWERED_REMINDER
        )
        start_cutoff_date = datetime.datetime.now() - wait_period

        recurrence_delay = datetime.timedelta(
            askbot_settings.UNANSWERED_REMINDER_FREQUENCY
        )
        max_emails = askbot_settings.MAX_UNANSWERED_REMINDERS
        end_cutoff_date = start_cutoff_date - (max_emails - 1)*recurrence_delay

        questions = models.Question.objects.exclude(
                                        closed = True
                                    ).exclude(
                                        deleted = True
                                    ).filter(
                                        added_at__lt = start_cutoff_date
                                    ).exclude(
                                        added_at__lt = end_cutoff_date
                                    ).filter(
                                        answer_count = 0
                                    ).order_by('-added_at')
        #for all users, excluding blocked
        #for each user, select a tag filtered subset
        #format the email reminder and send it
        for user in models.User.objects.exclude(status = 'b'):
            user_questions = questions.exclude(author = user)
            user_questions = user.get_tag_filtered_questions(user_questions)

            final_question_list = list()
            #todo: rewrite using query set filter
            #may be a lot more efficient
            for question in user_questions:
                activity_type = const.TYPE_ACTIVITY_UNANSWERED_REMINDER_SENT
                try:
                    activity = models.Activity.objects.get(
                        user = user,
                        question = question,
                        activity_type = activity_type
                    )
                    now = datetime.datetime.now()
                    if now < activity.active_at + recurrence_delay:
                        continue
                except models.Activity.DoesNotExist:
                    activity = models.Activity(
                        user = user,
                        question = question,
                        activity_type = activity_type,
                        content_object = question,
                    )
                activity.active_at = datetime.datetime.now()
                activity.save()
                final_question_list.append(question)

            question_count = len(final_question_list)
            if question_count == 0:
                continue

            tag_summary = get_tag_summary_from_questions(final_question_list)
            subject_line = ungettext(
                '%(question_count)d unanswered question about %(topics)s',
                '%(question_count)d unanswered questions about %(topics)s',
                question_count
            ) % {
                'question_count': question_count,
                'topics': tag_summary
            }

            body_text = '<ul>'
            for question in final_question_list:
                body_text += '<li><a href="%s%s?sort=latest">%s</a></li>' \
                            % (
                                askbot_settings.APP_URL,
                                question.get_absolute_url(),
                                question.title
                            )
            body_text += '</ul>'

            if DEBUG_THIS_COMMAND:
                print "User: %s<br>\nSubject:%s<br>\nText: %s<br>\n" % \
                    (user.email, subject_line, body_text)
            else:
                mail.send_mail(
                    subject_line = subject_line,
                    body_text = body_text,
                    recipient_list = (user.email,)
                )
