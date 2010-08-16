"""Tests database api - the basic data entry 
functions that happen on behalf of users

e.g. ``some_user.do_something(...)``
"""
from askbot.tests.utils import AskbotTestCase
from askbot import models
import datetime

class DBApiTests(AskbotTestCase):

    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.question = self.post_question()
        self.now = datetime.datetime.now()

    def post_answer(self, user = None, question = None):
        if user is None:
            user = self.user
        if question is None:
            question = self.question

        self.answer = super(DBApiTests, self).post_answer(
                                                user = user,
                                                question = question,
                                            )

    def assert_post_is_deleted(self, post):
        self.assertTrue(post.deleted == True)
        self.assertTrue(isinstance(post.deleted_by, models.User))
        self.assertTrue(post.deleted_at is not None)

    def assert_post_is_not_deleted(self, post):
        self.assertTrue(post.deleted == False)
        self.assertTrue(post.deleted_by == None)
        self.assertTrue(post.deleted_at == None)

    def test_flag_question(self):
        self.user.set_status('m')
        self.user.flag_post(self.question)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )

    def test_flag_answer(self):
        self.post_answer()
        self.user.set_status('m')
        self.user.flag_post(self.answer)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )

    def test_accept_best_answer(self):
        self.post_answer(user = self.other_user)
        self.user.accept_best_answer(self.answer)

    def test_delete_question(self):
        self.user.delete_question(self.question)
        self.assert_post_is_deleted(self.question)

    def test_restore_question(self):
        self.question.deleted = True
        self.question.deleted_by = self.user
        self.question.deleted_at = self.now
        self.question.save()
        self.user.restore_post(self.question)
        self.assert_post_is_not_deleted(self.question)

    def test_delete_answer(self):
        self.post_answer(question = self.question)
        self.user.delete_answer(self.answer)
        self.assert_post_is_deleted(self.answer)

    def test_restore_answer(self):
        self.post_answer()
        self.answer.deleted = True
        self.answer.deleted_by = self.user
        self.answer.deleted_at = self.now
        self.answer.save()
        self.user.restore_post(self.answer)
        self.assert_post_is_not_deleted(self.answer)

    def test_delete_question_with_answer_by_other(self):
        self.post_answer(user = self.other_user)
        self.user.delete_question(self.question)
        self.assert_post_is_deleted(self.question)
        answer_count = self.question.get_answers(user = self.user).count()
        answer = self.question.answers.all()[0]
        self.assert_post_is_not_deleted(answer)
        self.assertTrue(answer_count == 1)
        self.assertTrue(self.question.answer_count == 1)
