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
            self.user.get_flags().count(),
            1
        )

    def test_flag_answer(self):
        self.post_answer()
        self.user.set_status('m')
        self.user.flag_post(self.answer)
        self.assertEquals(
            self.user.get_flags().count(),
            1
        )

    def ask_anonymous_question(self):
        q = self.user.post_question(
                        is_anonymous = True,
                        body_text = 'hahahah',
                        title = 'aouaouaosuoa',
                        tags = 'test'
                    )
        return self.reload_object(q)

    def test_post_anonymous_question(self):
        q = self.ask_anonymous_question()
        self.assertTrue(q.is_anonymous)
        rev = q.revisions.all()[0]
        self.assertTrue(rev.is_anonymous)

    def test_reveal_asker_identity(self):
        q = self.ask_anonymous_question()
        self.other_user.set_status('m')
        self.other_user.save()
        self.other_user.edit_question(
                            question = q,
                            title = 'hahah',
                            body_text = 'hoeuaoea',
                            tags = 'aoeuaoeu',
                            revision_comment = 'hahahah'
                        )
        q.remove_author_anonymity()
        q = self.reload_object(q)
        self.assertFalse(q.is_anonymous)
        for rev in q.revisions.all():
            self.assertFalse(rev.is_anonymous)

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
        saved_question = models.Question.objects.get(id = self.question.id)
        self.assertEquals(
                saved_question.answer_count,
                0
            )

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
        saved_question = models.Question.objects.get(id = self.question.id)
        self.assertTrue(saved_question.answer_count == 1)

    def test_unused_tag_is_auto_deleted(self):
        self.user.retag_question(self.question, tags = 'one-tag')
        tag = models.Tag.objects.get(name='one-tag')
        self.assertEquals(tag.used_count, 1)
        self.assertEquals(tag.deleted, False)
        self.user.retag_question(self.question, tags = 'two-tag')

        count = models.Tag.objects.filter(name='one-tag').count()
        self.assertEquals(count, 0)
