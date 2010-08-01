"""
.. _on_screen_notification_tests:

:mod:`on_screen_notification_tests` -- Module for testing on-screen notifications
=================================================================================

.. automodule:: on_screen_notification_tests 
  .. moduleauthor:: Evgeny Fadeev <evgeny.fadeev@gmail.com>
"""
import datetime
import time
from django.test import TestCase
from askbot import models
from askbot import const
from askbot.tests.utils import create_user


def get_re_notif_after(timestamp):
    """returns query set with response notifications
    posted after the ``timestamp`` - a ``datetime.datetime`` instance
    """
    notifications = models.Activity.objects.filter(
            activity_type__in = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY,
            active_at__gte = timestamp
        )
    return notifications


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
        self.u11 = models.User.objects.get(id=self.u11.id)
        self.u12 = models.User.objects.get(id=self.u12.id)
        self.u13 = models.User.objects.get(id=self.u13.id)
        self.u14 = models.User.objects.get(id=self.u14.id)
        self.u21 = models.User.objects.get(id=self.u21.id)
        self.u22 = models.User.objects.get(id=self.u22.id)
        self.u23 = models.User.objects.get(id=self.u23.id)
        self.u24 = models.User.objects.get(id=self.u24.id)
        self.u31 = models.User.objects.get(id=self.u31.id)
        self.u32 = models.User.objects.get(id=self.u32.id)
        self.u33 = models.User.objects.get(id=self.u33.id)
        self.u34 = models.User.objects.get(id=self.u34.id)
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
        self.u11 = create_user('user11', 'user11@example.com', status='m')
        self.u12 = create_user('user12', 'user12@example.com', status='m')
        self.u13 = create_user('user13', 'user13@example.com', status='m')
        self.u14 = create_user('user14', 'user14@example.com', status='m')

        #users for first answer
        self.u21 = create_user('user21', 'user21@example.com', status='m')#post answer
        self.u22 = create_user('user22', 'user22@example.com', status='m')#edit answer
        self.u23 = create_user('user23', 'user23@example.com', status='m')
        self.u24 = create_user('user24', 'user24@example.com', status='m')

        #users for second answer
        self.u31 = create_user('user31', 'user31@example.com', status='m')#post answer
        self.u32 = create_user('user32', 'user32@example.com', status='m')#edit answer
        self.u33 = create_user('user33', 'user33@example.com', status='m')
        self.u34 = create_user('user34', 'user34@example.com', status='m')

        #a hack to initialize .users list
        self.reload_users()

        #pre-populate askbot with some content
        self.question = models.Question.objects.create_new(
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
        self.answer1 = models.Answer.objects.create_new(
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
        self.answer2 = models.Answer.objects.create_new(
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
        self.answer3 = models.Answer.objects.create_new(
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
        self.answer3 = models.Answer.objects.create_new(
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


