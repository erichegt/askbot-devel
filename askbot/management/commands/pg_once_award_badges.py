#!/usr/bin/env python
#encoding:utf-8
#-------------------------------------------------------------------------------
# Name:        Award badges command
# Purpose:     This is a command file croning in background process regularly to
#              query database and award badges for user's special acitivities.
#
# Author:      Mike, Sailing
#
# Created:     18/01/2009
# Copyright:   (c) Mike 2009
# Licence:     GPL V2
#-------------------------------------------------------------------------------

from datetime import datetime, date
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

BADGE_AWARD_TYPE_FIRST = {
    TYPE_ACTIVITY_MARK_OFFENSIVE : 7,
    TYPE_ACTIVITY_CANCEL_VOTE: 8,
    TYPE_ACTIVITY_VOTE_DOWN : 9,
    TYPE_ACTIVITY_UPDATE_QUESTION : 10,
    TYPE_ACTIVITY_UPDATE_ANSWER : 10,
    TYPE_ACTIVITY_UPDATE_TAGS : 11,
    TYPE_ACTIVITY_MARK_ANSWER : 12,
    TYPE_ACTIVITY_VOTE_UP : 14,
    TYPE_ACTIVITY_USER_FULL_UPDATED: 16

}

class Command(BaseCommand):
    def handle_noargs(self, **options):
        try:
            try:
                self.alpha_user()
                self.beta_user()
                self.first_type_award()
                self.first_ask_be_voted()
                self.first_answer_be_voted()
                self.first_answer_be_voted_10()
                self.vote_count_300()
                self.edit_count_100()
                self.comment_count_10()
            except Exception, e:
                print e
        finally:
            connection.close()

    def alpha_user(self):
        """
        Before Jan 25, 2009(Chinese New Year Eve and enter into Beta for CNProg), every registered user
        will be awarded the "Alpha" badge if he has any activities.
        """
        alpha_end_date = date(2009, 1, 25)
        if date.today() < alpha_end_date:
            badge = get_object_or_404(Badge, id=22)
            for user in User.objects.all():
                award = Award.objects.filter(user=user, badge=badge)
                if award and not badge.multiple:
                    continue
                activities = Activity.objects.filter(user=user)
                if len(activities) > 0:
                    new_award = Award(user=user, badge=badge)
                    new_award.save()

    def beta_user(self):
        """
        Before Feb 25, 2009, every registered user
        will be awarded the "Beta" badge if he has any activities.
        """
        beta_end_date = date(2009, 2, 25)
        if date.today() < beta_end_date:
            badge = get_object_or_404(Badge, id=33)
            for user in User.objects.all():
                award = Award.objects.filter(user=user, badge=badge)
                if award and not badge.multiple:
                    continue
                activities = Activity.objects.filter(user=user)
                if len(activities) > 0:
                    new_award = Award(user=user, badge=badge)
                    new_award.save()

    def first_type_award(self):
        """
        This will award below badges for users first behaviors:

        (7, '???', 3, '???', '?????????', 0, 0),
        (8, '???', 3, '???', '???????', 0, 0),
        (9, '???', 3, '???', '??????', 0, 0),
        (10, '??', 3, '??', '???????', 0, 0),
        (11, '??', 3, '??', '???????', 0, 0),
        (12, '??', 3, '??', '???????', 0, 0),
        (14, '???', 3, '???', '??????', 0, 0),
        (16, '????', 3, '????', '????????????', 0, 0),
        """
        activity_types = ','.join('%s' % item for item in BADGE_AWARD_TYPE_FIRST.keys())
        # ORDER BY user_id, activity_type
        query = "SELECT id, user_id, activity_type, content_type_id, object_id FROM activity WHERE not is_auditted AND activity_type IN (%s) ORDER BY user_id, activity_type" % activity_types

        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            # collect activity_id in current process
            activity_ids = []
            last_user_id = 0
            last_activity_type = 0
            for row in rows:
                activity_ids.append(row[0])
                user_id = row[1]
                activity_type = row[2]
                content_type_id = row[3]
                object_id = row[4]

                # if the user and activity are same as the last, continue
                if user_id == last_user_id and activity_type == last_activity_type:
                    continue;

                user = get_object_or_404(User, id=user_id)
                badge = get_object_or_404(Badge, id=BADGE_AWARD_TYPE_FIRST[activity_type])
                content_type = get_object_or_404(ContentType, id=content_type_id)

                count = Award.objects.filter(user=user, badge=badge).count()
                if count and not badge.multiple:
                    continue
                else:
                    # new award
                    award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                    award.save()

                # set the current user_id and activity_type to last
                last_user_id = user_id
                last_activity_type = activity_type

            # update processed rows to auditted
            self.update_activities_auditted(cursor, activity_ids)
        finally:
            cursor.close()

    def first_ask_be_voted(self):
        """
        For user asked question and got first upvote, we award him following badge:

        (13, '??', 3, '??', '???????????????', 0, 0),
        """
        query = "SELECT act.user_id, q.vote_up_count, act.object_id FROM " \
                    "activity act, question q WHERE act.activity_type = %s AND " \
                    "act.object_id = q.id AND " \
                    "act.user_id NOT IN (SELECT distinct user_id FROM award WHERE badge_id = %s)" % (TYPE_ACTIVITY_ASK_QUESTION, 13)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            badge = get_object_or_404(Badge, id=13)
            content_type = ContentType.objects.get_for_model(Question)
            awarded_users = []
            for row in rows:
                user_id = row[0]
                vote_up_count = row[1]
                object_id = row[2]
                if vote_up_count > 0 and user_id not in awarded_users:
                    user = get_object_or_404(User, id=user_id)
                    award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                    award.save()
                    awarded_users.append(user_id)
        finally:
            cursor.close()

    def first_answer_be_voted(self):
        """
        When user answerd questions and got first upvote, we award him following badge:

        (15, '??', 3, '??', '??????????????????', 0, 0),
        """
        query = "SELECT act.user_id, a.vote_up_count, act.object_id FROM " \
                    "activity act, answer a WHERE act.activity_type = %s AND " \
                    "act.object_id = a.id AND " \
                    "act.user_id NOT IN (SELECT distinct user_id FROM award WHERE badge_id = %s)" % (TYPE_ACTIVITY_ANSWER, 15)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            awarded_users = []
            badge = get_object_or_404(Badge, id=15)
            content_type = ContentType.objects.get_for_model(Answer)
            for row in rows:
                user_id = row[0]
                vote_up_count = row[1]
                object_id = row[2]
                if vote_up_count > 0 and user_id not in awarded_users:
                    user = get_object_or_404(User, id=user_id)
                    award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                    award.save()
                    awarded_users.append(user_id)
        finally:
            cursor.close()

    def first_answer_be_voted_10(self):
        """
        (32, '???', 2, '???', '??????????10???', 0, 0)
        """
        query = "SELECT act.user_id, act.object_id FROM " \
                    "activity act, answer a WHERE act.object_id = a.id AND " \
                    "act.activity_type = %s AND " \
                    "a.vote_up_count >= 10 AND " \
                    "act.user_id NOT IN (SELECT user_id FROM award WHERE badge_id = %s)" % (TYPE_ACTIVITY_ANSWER, 32)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            awarded_users = []
            badge = get_object_or_404(Badge, id=32)
            content_type = ContentType.objects.get_for_model(Answer)
            for row in rows:
                user_id = row[0]
                if user_id not in awarded_users:
                    user = get_object_or_404(User, id=user_id)
                    object_id = row[1]
                    award = Award(user=user, badge=badge, content_type=content_type, object_id=object_id)
                    award.save()
                    awarded_users.append(user_id)
        finally:
            cursor.close()

    def vote_count_300(self):
        """
        (26, '????', 2, '????', '??300???', 0, 0)
        """
        query = "SELECT count(*) as vote_count, user_id FROM activity WHERE " \
                    "activity_type = %s OR " \
                    "activity_type = %s AND " \
                    "user_id NOT IN (SELECT user_id FROM award WHERE badge_id = %s) " \
                    "GROUP BY user_id HAVING count(*) >= 300" % (TYPE_ACTIVITY_VOTE_UP, TYPE_ACTIVITY_VOTE_DOWN, 26)

        self.__award_for_count_num(query, 26)

    def edit_count_100(self):
        """
        (27, '????', 2, '????', '???100???', 0, 0)
        """
        query = "SELECT count(*) as vote_count, user_id FROM activity WHERE " \
                    "activity_type = %s OR " \
                    "activity_type = %s AND " \
                    "user_id NOT IN (SELECT user_id FROM award WHERE badge_id = %s) " \
                    "GROUP BY user_id HAVING count(*) >= 100" % (TYPE_ACTIVITY_UPDATE_QUESTION, TYPE_ACTIVITY_UPDATE_ANSWER, 27)

        self.__award_for_count_num(query, 27)

    def comment_count_10(self):
        """
        (5, '???', 3, '???', '??10???', 0, 0),
        """
        query = "SELECT count(*) as vote_count, user_id FROM activity WHERE " \
                    "activity_type = %s OR " \
                    "activity_type = %s AND " \
                    "user_id NOT IN (SELECT user_id FROM award WHERE badge_id = %s) " \
                    "GROUP BY user_id HAVING count(*) >= 10" % (TYPE_ACTIVITY_COMMENT_QUESTION, TYPE_ACTIVITY_COMMENT_ANSWER, 5)
        self.__award_for_count_num(query, 5)

    def __award_for_count_num(self, query, badge):
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            awarded_users = []
            badge = get_object_or_404(Badge, id=badge)
            for row in rows:
                vote_count = row[0]
                user_id = row[1]

                if user_id not in awarded_users:
                    user = get_object_or_404(User, id=user_id)
                    award = Award(user=user, badge=badge)
                    award.save()
                    awarded_users.append(user_id)
        finally:
            cursor.close()

def main():
    pass

if __name__ == '__main__':
    main()
