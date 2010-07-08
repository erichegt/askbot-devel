"""
.. _tests:

:mod:`tests` -- Module for testing Askbot 
==========================================

.. automodule:: tests 
  .. moduleauthor:: Evgeny Fadeev <evgeny.fadeev@gmail.com>
"""
import copy
import datetime
import time
import django.core.mail
from django.conf import settings as django_settings
from django.test import TestCase
from django.template import defaultfilters
from django.core import management
from django.core.urlresolvers import reverse
from askbot.models import User, Question, Answer, Activity
from askbot.models import EmailFeedSetting
from askbot import const

def create_user(
            username = None, 
            email = None, 
            notification_schedule = None,
            date_joined = None
        ):
    """Creates a user and sets default update subscription
    settings"""
    user = User.objects.create_user(username, email)
    if date_joined is not None:
        user.date_joined = date_joined
        user.save()
    if notification_schedule == None:
        notification_schedule = EmailFeedSetting.NO_EMAIL_SCHEDULE
        
    for feed_type, frequency in notification_schedule.items():
        feed = EmailFeedSetting(
                        feed_type = feed_type,
                        frequency = frequency,
                        subscriber = user
                    )
        feed.save()
    return user

def get_re_notif_after(timestamp):
    notifications = Activity.objects.filter(
            activity_type__in = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY,
            active_at__gte = timestamp
        )
    return notifications

class EmailAlertTests(TestCase):
    """Base class for testing delayed Email notifications 
    that are triggered by the send_email_alerts
    command

    this class tests cases where target user has no subscriptions
    that is all subscriptions off

    subclasses should redefine initial data via the static
    class member    this class tests cases where target user has no subscriptions
    that is all subscriptions off

    this class also defines a few utility methods that do
    not run any tests themselves

    class variables:

    * notification_schedule
    * setup_timestamp
    * visit_timestamp
    * expected_results

    should be set in subclasses to reuse testing code
    """

    def send_alerts(self):
        """runs the send_email_alerts management command
        and makes a shortcut access to the outbox
        """
        #make sure tha we are not sending email for real
        #this setting must be present in settings.py
        assert(
            django_settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
        )
        management.call_command('send_email_alerts')

    def setUp(self):
        """generic pre-test setup method:
        
        * creates user who is to post stuff
        * creates user who is targeted for this update
        * subclass must subscribe receiving user
          with frequency that is to be tested
          in addition making to any other specific setup
          manipulations
        """
        #empty email subscription schedule
        #no email is sent
        self.notification_schedule = copy.deepcopy(EmailFeedSetting.NO_EMAIL_SCHEDULE)
        #timestamp to use for the setup
        #functions
        self.setup_timestamp = datetime.datetime.now()

        #must call this after setting up the notification schedule
        #and only in this class, any subclasses
        #must call this setUp() first thing
        #before setting their own notification schedule
        #and after that - setUpUsers()
        self.setUpUsers()
        
        #timestamp to use for the question visit
        #by the target user
        #if this timestamp is None then there will be no visit
        #otherwise question will be visited by the target user
        #at that time
        self.visit_timestamp = None

        #dictionary to hols expected results for each test
        #actual data@is initialized in the code just before the function
        #or in the body of the subclass
        self.expected_results = dict()

        #fill out expected result for each test
        self.expected_results['q_ask'] = { 'message_count': 0, }
        self.expected_results['question_comment'] = { 'message_count': 0, }

    def setUpUsers(self):
        self.other_user = create_user(
            username = 'other', 
            email = 'other@domain.com',
            date_joined = self.setup_timestamp
        )
        self.target_user = create_user(
            username = 'target',
            email = 'target@domain.com',
            notification_schedule = self.notification_schedule,
            date_joined = self.setup_timestamp
        )

    def post_comment(
                self,
                author = None,
                parent_post = None,
                body_text = 'dummy test comment',
                timestamp = None
            ):
        """posts and returns a comment to parent post, uses 
        now timestamp if not given, dummy body_text 
        author is required
        """
        comment = author.post_comment(
                        parent_post = parent_post,
                        body_text = body_text,
                        timestamp = timestamp,
                    )
        return comment

    def post_question(
                self, 
                author = None, 
                timestamp = None,
                title = 'test question title',
                body_text = 'test question body',
                tags = 'test',
            ):
        """post a question with dummy content
        and return it
        """
        return author.post_question(
                            title = 'test question',
                            body_text = 'test question body',
                            tags = 'test',
                            timestamp = timestamp
                        )

    def maybe_visit_question(self, user = None):
        """visits question on behalf of a given user and applies 
        a timestamp set in the class attribute ``visit_timestamp``

        if ``visit_timestamp`` is None, then visit is skipped

        parameter ``user`` is optional if not given, the visit will occur
        on behalf of the user stored in the class attribute ``target_user``
        """
        if self.visit_timestamp:
            if user is None:
                user = self.target_user

            user.visit_post(
                        question = question,
                        timestamp = self.visit_timestamp
                    )

    def post_answer(
                self,
                question = None,
                author = None,
                body_text = 'test answer body',
                timestamp = None
            ):
        """post answer with dummy content and return it
        """
        return author.post_answer(
                    question = question,
                    body_text = body_text,
                    timestamp = timestamp
                )

    def check_results(self, test_key = None):
        if test_key is None:
            raise ValueError('test_key parameter is required')
        expected = self.expected_results[test_key]
        outbox = django.core.mail.outbox
        self.assertEqual(len(outbox), expected['message_count'])
        if expected['message_count'] > 0:
            if len(outbox) > 0:
                self.assertEqual(
                            outbox[0].recipients()[0], 
                            self.target_user.email
                        )

    def test_question_comment(self):
        """target user posts question other user posts a comment
        target user does or does not receive email notification
        depending on the setup parameters

        in the base class user does not receive a notification
        """
        question = self.post_question(
                    author = self.target_user,
                    timestamp = self.setup_timestamp,
                )
        self.post_comment(
                    author = self.other_user,
                    parent_post = question,
                    timestamp = self.setup_timestamp
                )
        self.maybe_visit_question(question)
        self.send_alerts()
        self.check_results('question_comment')

    def test_q_ask(self):
        """target user posts question
        other user answer the question
        """
        question = self.post_question(
                    author = self.target_user,
                    timestamp = self.setup_timestamp,
                )
        answer = self.post_answer(
                    question = question,
                    author = self.other_user,
                    timestamp = self.setup_timestamp + datetime.timedelta(1)
                )
        self.maybe_visit_question(question)
        self.send_alerts()
        self.check_results('q_ask')

class WeeklyQAskEmailAlertTests(EmailAlertTests):
    def setUp(self):
        self.notification_schedule = copy.deepcopy(EmailFeedSetting.NO_EMAIL_SCHEDULE)
        self.notification_schedule['q_ask'] = 'w'
        self.setup_timestamp = datetime.datetime.now() - datetime.timedelta(14)

        self.setUpUsers() #must call create_users after super.setUp() and schedule

        self.visit_timestamp = None

        self.expected_results = dict()
        self.expected_results['q_ask'] = {'message_count': 1}
        self.expected_results['question_comment'] = {'message_count': 0}

class WeeklyMentionsAndCommentsEmailAlertTests(EmailAlertTests):
    def setUp(self):
        self.notification_schedule = copy.deepcopy(EmailFeedSetting.NO_EMAIL_SCHEDULE)
        self.notification_schedule['m_and_c'] = 'w'
        self.setup_timestamp = datetime.datetime.now() - datetime.timedelta(14)

        self.setUpUsers()

        self.visit_timestamp = None

        self.expected_results = dict()
        self.expected_results['q_ask'] = {'message_count': 0}
        self.expected_results['question_comment'] = {'message_count': 1}

class OnScreenUpdateNotificationTests(TestCase):
    """Test update notifications that are displayed on
    screen in the user profile responses view
    and "the red envelope"
    """

    def reset_response_counts(self):
        self.reload_users()
        for user in self.users:
            user.response_count = 0
            user.save()

    def reload_users(self):
        self.u11 = User.objects.get(id=self.u11.id)
        self.u12 = User.objects.get(id=self.u12.id)
        self.u13 = User.objects.get(id=self.u13.id)
        self.u14 = User.objects.get(id=self.u14.id)
        self.u21 = User.objects.get(id=self.u21.id)
        self.u22 = User.objects.get(id=self.u22.id)
        self.u23 = User.objects.get(id=self.u23.id)
        self.u24 = User.objects.get(id=self.u24.id)
        self.u31 = User.objects.get(id=self.u31.id)
        self.u32 = User.objects.get(id=self.u32.id)
        self.u33 = User.objects.get(id=self.u33.id)
        self.u34 = User.objects.get(id=self.u34.id)
        self.users = [
            self.u11,
            self.u12,
            self.u13,
            self.u14,
            self.u21,
            self.u22,
            self.u23,
            self.u24,
            self.u31,
            self.u32,
            self.u33,
            self.u34,
        ]

    def setUp(self):
        #users for the question
        self.u11 = create_user('user11', 'user11@example.com')
        self.u12 = create_user('user12', 'user12@example.com')
        self.u13 = create_user('user13', 'user13@example.com')
        self.u14 = create_user('user14', 'user14@example.com')

        #users for first answer
        self.u21 = create_user('user21', 'user21@example.com')#post answer
        self.u22 = create_user('user22', 'user22@example.com')#edit answer
        self.u23 = create_user('user23', 'user23@example.com')
        self.u24 = create_user('user24', 'user24@example.com')

        #users for second answer
        self.u31 = create_user('user31', 'user31@example.com')#post answer
        self.u32 = create_user('user32', 'user32@example.com')#edit answer
        self.u33 = create_user('user33', 'user33@example.com')
        self.u34 = create_user('user34', 'user34@example.com')

        #a hack to initialize .users list
        self.reload_users()

        #pre-populate askbot with some content
        self.question = Question.objects.create_new(
                            title = 'test question',
                            author = self.u11,
                            added_at = datetime.datetime.now(),
                            wiki = False,
                            tagnames = 'test', 
                            text = 'hey listen up',
                        )
        self.comment12 = self.question.add_comment(
                            user = self.u12,
                            comment = 'comment12'
                        )
        self.comment13 = self.question.add_comment(
                            user = self.u13,
                            comment = 'comment13'
                        )
        self.answer1 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u21,
                            added_at = datetime.datetime.now(),
                            text = 'answer1'
                        )
        self.comment22 = self.answer1.add_comment(
                            user = self.u22,
                            comment = 'comment22'
                        )
        self.comment23 = self.answer1.add_comment(
                            user = self.u23,
                            comment = 'comment23'
                        )
        self.answer2 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u31,
                            added_at = datetime.datetime.now(),
                            text = 'answer2'
                        )
        self.comment32 = self.answer2.add_comment(
                            user = self.u32,
                            comment = 'comment32'
                        )
        self.comment33 = self.answer2.add_comment(
                            user = self.u33,
                            comment = 'comment33'
                        )

    def post_then_delete_answer_comment(self):
        pass

    def post_then_delete_answer(self):
        pass

    def post_then_delete_question_comment(self):
        pass

    def post_mention_in_question_then_delete(self):
        pass

    def post_mention_in_answer_then_delete(self):
        pass

    def post_mention_in_question_then_edit_out(self):
        pass

    def post_mention_in_answer_then_edit_out(self):
        pass

    def test_post_mention_in_question_comment_then_delete(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        comment = self.question.add_comment(
                            user = self.u11,
                            comment = '@user12 howyou doin?',
                            added_at = timestamp
                        )
        comment.delete()
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 0)
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        comment = self.answer1.add_comment(
                            user = self.u21,
                            comment = 'hey @user22 blah',
                            added_at = timestamp
                        )
        comment.delete()
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 0)
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_comments(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u21,
                            comment = 'self-comment 2',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u22, self.u23]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 1, 1, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_question1(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment @user11',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_question2(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment @user11 blah',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_answer(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u21,
                            comment = 'self-comment 1 @user21',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u22, self.u23]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 1, 1, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_comments_to_post_authors(self):
        self.question.apply_edit(
                        edited_by = self.u14,
                        text = 'now much better',
                        comment = 'improved text'
                    )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u12,
                            comment = 'self-comment 1',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u13, self.u14]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 0, 1, 1,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )
        self.answer1.apply_edit(
                        edited_by = self.u24,
                        text = 'now much better',
                        comment = 'improved text'
                    )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u22,
                            comment = 'self-comment 1',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u21, self.u23, self.u24]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 1, 0, 1, 1,
                 0, 0, 0, 0,
            ]
        )

    def test_question_edit(self):
        """when question is edited
        response receivers are question authors, commenters
        and answer authors, but not answer commenters
        """
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.apply_edit(
                        edited_by = self.u14,
                        text = 'waaay better question!',
                        comment = 'improved question',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u12, self.u13, self.u21, self.u31])
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 0, 0, 0,
                 1, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.apply_edit(
                        edited_by = self.u31,
                        text = 'waaay even better question!',
                        comment = 'improved question',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u12, self.u13, self.u14, self.u21])
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 1,
                 1, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_answer_edit(self):
        """
        """
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.apply_edit(
                        edited_by = self.u24,
                        text = 'waaay better answer!',
                        comment = 'improved answer1',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u11, self.u12, self.u13, 
                    self.u21, self.u22, self.u23,
                    self.u31
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 1, 1, 0,
                 1, 0, 0, 0,
            ]
        )

    def test_new_answer(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer3 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u11,
                            added_at = timestamp,
                            text = 'answer3'
                        )
        time_end = datetime.datetime.now()
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u12, self.u13, 
                    self.u21, self.u31
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 1, 0, 0, 0,
                 1, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer3 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u31,
                            added_at = timestamp,
                            text = 'answer4'
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u11, self.u12, self.u13, 
                    self.u21
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )


class AnonymousVisitorTests(TestCase):
    fixtures = ['tmp/fixture1.json', ]

    def test_index(self):
        #todo: merge this with all reader url tests
        print 'trying to reverse index'
        response = self.client.get(reverse('index'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.failUnless(len(response.redirect_chain) == 1)
        self.failUnless(response.redirect_chain[0][0].endswith('/questions/'))
        c = response.context[0]
        t = response.template[0]
        self.assertEqual(t.name, 'questions.html')
        print 'index works'

    def test_reader_urls(self):
        """test all reader views thoroughly
        on non-crashiness (no correcteness tests here)
        """

        def try_url(
                url_name, status_code=200, template=None, 
                kwargs={}, redirect_url=None, follow=False,
                data = {},
            ):
            url = reverse(url_name, kwargs = kwargs)
            url_info = 'getting url %s' % url
            if data:
                url_info += '?' + '&'.join(['%s=%s' % (k, v) for k, v in data.iteritems()])
            print url_info

            r = self.client.get(url, data=data, follow=follow)
            if hasattr(self.client, 'redirect_chain'):
                print 'redirect chain: %s' % ','.join(self.client.redirect_chain)

            self.assertEqual(r.status_code, status_code)

            if template:
                #asuming that there is more than one template
                print 'templates are %s' % ','.join([t.name for t in r.template])
                self.assertEqual(r.template[0].name, template)

        try_url('sitemap')
        try_url('feeds', kwargs={'url':'rss'})
        try_url('about', template='about.html')
        try_url('privacy', template='privacy.html')
        try_url('logout', template='logout.html')
        try_url('user_signin', template='authopenid/signin.html')
        #todo: test different tabs
        try_url('tags', template='tags.html')
        try_url('tags', data={'sort':'name'}, template='tags.html')
        try_url('tags', data={'sort':'used'}, template='tags.html')
        try_url('badges', template='badges.html')
        try_url(
                'answer_revisions', 
                template='revisions_answer.html',
                kwargs={'id':38}
            )
        #todo: test different sort methods and scopes
        try_url(
                'questions',
                template='questions.html'
            )
        try_url(
                'questions',
                data={'start_over':'true'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'all'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'favorite'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'latest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'oldest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'active'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'inactive'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'hottest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'coldest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'mostvoted'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'leastvoted'},
                template='questions.html'
            )
        try_url(
                'question',
                kwargs={'id':1},
            )
        try_url(
                'question',
                kwargs={'id':2},
            )
        try_url(
                'question',
                kwargs={'id':3},
            )
        try_url(
                'question_revisions',
                kwargs={'id':17},
                template='revisions_question.html'
            )
        try_url('users', template='users.html')
        #todo: really odd naming conventions for sort methods
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':1},
            )
        try_url(
                'edit_user',
                template='authopenid/signin.html',
                kwargs={'id':4},
                status_code=200,
                follow=True,
            )
        user = User.objects.get(id=2)
        name_slug = defaultfilters.slugify(user.username)
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'stats'}, 
            template='user_stats.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'recent'}, 
            template='user_recent.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'responses'}, 
            status_code=404,
            template='404.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'reputation'}, 
            template='user_reputation.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'votes'}, 
            status_code=404,
            template='404.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'favorites'}, 
            template='user_favorites.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'email_subscriptions'}, 
            status_code=404,
            template='404.html'
        )
