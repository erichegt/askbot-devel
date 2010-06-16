#!/usr/bin/env python
#encoding:utf-8
#-------------------------------------------------------------------------------
# Name:        Award badges command
# Purpose:     This is a command file croning in background process regularly to
#              query database and award badges for user's special acitivities.
#
# Author:      Mike, Sailing
#
# Created:     22/01/2009
# Copyright:   (c) Mike 2009
# Licence:     GPL V2
#-------------------------------------------------------------------------------

from datetime import datetime, date
from django.core.management.base import NoArgsCommand
from django.db import connection
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from askbot.models import *
from askbot.const import *
from pg_base_command import BaseCommand
"""
(1, '????', 3, '????', '?????3?????????', 1, 0),
(2, '????', 3, '????', '?????3?????????', 1, 0),
(3, '????', 3, '????', '????10???', 1, 0),
(4, '????', 3, '????', '????10???', 1, 0),
(5, '???', 3, '???', '??10???', 0, 0),
(6, '????', 3, '????', '????????1000??', 1, 0),
(7, '???', 3, '???', '?????????', 0, 0),
(8, '???', 3, '???', '???????', 0, 0),
(9, '???', 3, '???', '??????', 0, 0),
(10, '??', 3, '??', '???????', 0, 0),
(11, '??', 3, '??', '???????', 0, 0),
(12, '??', 3, '??', '???????', 0, 0),
(13, '??', 3, '??', '???????????????', 0, 0),
(14, '???', 3, '???', '??????', 0, 0),
(15, '??', 3, '??', '??????????????????', 0, 0),
(16, '????', 3, '????', '????????????', 0, 0),
(17, '????', 3, '????', '??????????3??????', 1, 0),
(18, '??????', 1, '??????', '????100????', 1, 0),
(19, '??????', 1, '??????', '????100????', 1, 0),
(20, '???', 1, '???', '???100?????', 1, 0),
(21, '????', 1, '????', '????????10000??', 1, 0),
(22, 'alpha??', 2, 'alpha??', '?????????', 0, 0),
(23, '????', 2, '????', '????25????', 1, 0),
(24, '????', 2, '????', '????25????', 1, 0),
(25, '?????', 2, '?????', '???25?????', 1, 0),
(26, '????', 2, '????', '??300???', 0, 0),
(27, '????', 2, '????', '???100???', 0, 0),
(28, '??', 2, '??', '?????????', 0, 0),
(29, '??', 2, '??', '???????????', 0, 0),
(30, '??', 2, '??', '?????????', 0, 0),
(31, '??????', 2, '??????', '????????2500??', 1, 0),
(32, '???', 2, '???', '??????????10???', 0, 0),
(33, 'beta??', 2, 'beta??', 'beta??????', 0, 0),
(34, '??', 2, '??', '?????????????40??', 1, 0),
(35, '??', 2, '??', '???60??????????5???', 1, 0),
(36, '????', 2, '????', '??????50???????', 1, 0);


TYPE_ACTIVITY_ASK_QUESTION=1
TYPE_ACTIVITY_ANSWER=2
TYPE_ACTIVITY_COMMENT_QUESTION=3
TYPE_ACTIVITY_COMMENT_ANSWER=4
TYPE_ACTIVITY_UPDATE_QUESTION=5
TYPE_ACTIVITY_UPDATE_ANSWER=6
TYPE_ACTIVITY_PRIZE=7
TYPE_ACTIVITY_MARK_ANSWER=8
TYPE_ACTIVITY_VOTE_UP=9
TYPE_ACTIVITY_VOTE_DOWN=10
TYPE_ACTIVITY_CANCEL_VOTE=11
TYPE_ACTIVITY_DELETE_QUESTION=12
TYPE_ACTIVITY_DELETE_ANSWER=13
TYPE_ACTIVITY_MARK_OFFENSIVE=14
TYPE_ACTIVITY_UPDATE_TAGS=15
TYPE_ACTIVITY_FAVORITE=16
TYPE_ACTIVITY_USER_FULL_UPDATED = 17
"""

class Command(BaseCommand):
    def handle_noargs(self, **options):
        try:
            try:
                self.delete_question_be_voted_up_3()
                self.delete_answer_be_voted_up_3()
                self.delete_question_be_vote_down_3()
                self.delete_answer_be_voted_down_3()
                self.answer_be_voted_up_10()
                self.question_be_voted_up_10()
                self.question_view_1000()
                self.answer_self_question_be_voted_up_3()
                self.answer_be_voted_up_100()
                self.question_be_voted_up_100()
                self.question_be_favorited_100()
                self.question_view_10000()
                self.answer_be_voted_up_25()
                self.question_be_voted_up_25()
                self.question_be_favorited_25()
                self.question_view_2500()
                self.answer_be_accepted_and_voted_up_40()
                self.question_be_answered_after_60_days_and_be_voted_up_5()
                self.created_tag_be_used_in_question_50()
            except Exception, e:
                print e
        finally:
            connection.close()

    def delete_question_be_voted_up_3(self):
        """
        (1, '????', 3, '????', '?????3?????????', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM activity act, question q WHERE act.object_id = q.id AND\
                act.activity_type = %s AND\
                q.vote_up_count >=3 AND \
                not act.is_auditted" % (TYPE_ACTIVITY_DELETE_QUESTION)
        self.__process_activities_badge(query, 1, Question)

    def delete_answer_be_voted_up_3(self):
        """
        (1, '????', 3, '????', '?????3?????????', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM activity act, answer an WHERE act.object_id = an.id AND\
                act.activity_type = %s AND\
                an.vote_up_count >=3 AND \
                not act.is_auditted" % (TYPE_ACTIVITY_DELETE_ANSWER)
        self.__process_activities_badge(query, 1, Answer)

    def delete_question_be_vote_down_3(self):
        """
        (2, '????', 3, '????', '?????3?????????', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM activity act, question q WHERE act.object_id = q.id AND\
                act.activity_type = %s AND\
                q.vote_down_count >=3 AND \
                not act.is_auditted" % (TYPE_ACTIVITY_DELETE_QUESTION)
        content_type = ContentType.objects.get_for_model(Question)
        self.__process_activities_badge(query, 2, Question)

    def delete_answer_be_voted_down_3(self):
        """
        (2, '????', 3, '????', '?????3?????????', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM activity act, answer an WHERE act.object_id = an.id AND\
                act.activity_type = %s AND\
                an.vote_down_count >=3 AND \
                not act.is_auditted" % (TYPE_ACTIVITY_DELETE_ANSWER)
        self.__process_activities_badge(query, 2, Answer)

    def answer_be_voted_up_10(self):
        """
        (3, '????', 3, '????', '????10???', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM \
                    activity act, answer a WHERE act.object_id = a.id AND\
                    act.activity_type = %s AND \
                    a.vote_up_count >= 10 AND\
                    not act.is_auditted" % (TYPE_ACTIVITY_ANSWER)
        self.__process_activities_badge(query, 3, Answer)

    def question_be_voted_up_10(self):
        """
        (4, '????', 3, '????', '????10???', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM \
                    activity act, question q WHERE act.object_id = q.id AND\
                    act.activity_type = %s AND \
                    q.vote_up_count >= 10 AND\
                    not act.is_auditted" % (TYPE_ACTIVITY_ASK_QUESTION)
        self.__process_activities_badge(query, 4, Question)

    def question_view_1000(self):
        """
        (6, '????', 3, '????', '????????1000??', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM \
                    activity act, question q WHERE act.activity_type = %s AND\
                    act.object_id = q.id AND \
                    q.view_count >= 1000 AND\
                    act.object_id NOT IN \
                        (SELECT object_id FROM award WHERE award.badge_id = %s)" % (TYPE_ACTIVITY_ASK_QUESTION, 6)
        self.__process_activities_badge(query, 6, Question, False)

    def answer_self_question_be_voted_up_3(self):
        """
        (17, '????', 3, '????', '??????????3??????', 1, 0),
        """
        query = "SELECT act.id, act.user_id, act.object_id FROM \
                    activity act, answer an WHERE act.activity_type = %s AND\
                    act.object_id = an.id AND\
                    an.vote_up_count >= 3 AND\
                    act.user_id = (SELECT user_id FROM question q WHERE q.id = an.question_id) AND\
                    act.object_id NOT IN \
                        (SELECT object_id FROM award WHERE award.badge_id = %s)" % (TYPE_ACTIVITY_ANSWER, 17)
        self.__process_activities_badge(query, 17, Question, False)

    def answer_be_voted_up_100(self):
        """
        (18, '??????', 1, '??????', '????100????', 1, 0),
        """
        query = "SELECT an.id, an.author_id FROM answer an WHERE an.vote_up_count >= 100 AND an.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (18)

        self.__process_badge(query, 18, Answer)

    def question_be_voted_up_100(self):
        """
        (19, '??????', 1, '??????', '????100????', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.vote_up_count >= 100 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (19)

        self.__process_badge(query, 19, Question)

    def question_be_favorited_100(self):
        """
        (20, '???', 1, '???', '???100?????', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.favourite_count >= 100 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (20)

        self.__process_badge(query, 20, Question)

    def question_view_10000(self):
        """
        (21, '????', 1, '????', '????????10000??', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.view_count >= 10000 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (21)

        self.__process_badge(query, 21, Question)

    def answer_be_voted_up_25(self):
        """
        (23, '????', 2, '????', '????25????', 1, 0),
        """
        query = "SELECT a.id, a.author_id FROM answer a WHERE a.vote_up_count >= 25 AND a.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (23)

        self.__process_badge(query, 23, Answer)

    def question_be_voted_up_25(self):
        """
        (24, '????', 2, '????', '????25????', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.vote_up_count >= 25 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (24)

        self.__process_badge(query, 24, Question)

    def question_be_favorited_25(self):
        """
        (25, '?????', 2, '?????', '???25?????', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.favourite_count >= 25 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (25)

        self.__process_badge(query, 25, Question)

    def question_view_2500(self):
        """
        (31, '??????', 2, '??????', '????????2500??', 1, 0),
        """
        query = "SELECT q.id, q.author_id FROM question q WHERE q.view_count >= 2500 AND q.id NOT IN \
                (SELECT object_id FROM award WHERE award.badge_id = %s)" % (31)

        self.__process_badge(query, 31, Question)

    def answer_be_accepted_and_voted_up_40(self):
        """
        (34, '??', 2, '??', '?????????????40??', 1, 0),
        """
        query = "SELECT a.id, a.author_id FROM answer a WHERE a.vote_up_count >= 40 AND\
                    a.accepted AND\
                    a.id NOT IN \
                    (SELECT object_id FROM award WHERE award.badge_id = %s)" % (34)

        self.__process_badge(query, 34, Answer)

    def question_be_answered_after_60_days_and_be_voted_up_5(self):
        """
        (35, '??', 2, '??', '???60??????????5???', 1, 0),
        """
        query = "SELECT a.id, a.author_id FROM question q, answer a WHERE q.id = a.question_id AND\
                    (a.added_at + '60 day'::INTERVAL) >= q.added_at AND\
                    a.vote_up_count >= 5 AND \
                    a.id NOT IN \
                    (SELECT object_id FROM award WHERE award.badge_id = %s)" % (35)

        self.__process_badge(query, 35, Answer)

    def created_tag_be_used_in_question_50(self):
        """
        (36, '????', 2, '????', '??????50???????', 1, 0);
        """
        query = "SELECT t.id, t.created_by_id FROM tag t, auth_user u WHERE t.created_by_id = u.id AND \
                    t. used_count >= 50 AND \
                    t.id NOT IN \
                    (SELECT object_id FROM award WHERE award.badge_id = %s)" % (36)

        self.__process_badge(query, 36, Tag)

    def __process_activities_badge(self, query, badge, content_object, update_auditted=True):
        content_type = ContentType.objects.get_for_model(content_object)

        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            if update_auditted:
                activity_ids = []
            badge = get_object_or_404(Badge, id=badge)
            for row in rows:
                activity_id = row[0]
                user_id = row[1]
                object_id = row[2]

                user = get_object_or_404(User, id=user_id)
                award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                award.save()

                if update_auditted:
                    activity_ids.append(activity_id)

            if update_auditted:
                self.update_activities_auditted(cursor, activity_ids)
        finally:
            cursor.close()

    def __process_badge(self, query, badge, content_object):
        content_type = ContentType.objects.get_for_model(Answer)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            badge = get_object_or_404(Badge, id=badge)
            for row in rows:
                object_id = row[0]
                user_id = row[1]

                user = get_object_or_404(User, id=user_id)
                award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                award.save()
        finally:
            cursor.close()
