from askbot.tests.utils import AskbotTestCase
from askbot.models.post import PostRevision

from django.test.client import Client
from django.core.urlresolvers import reverse

class MiscTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u2 = self.create_user(username='user2')
        self.u3 = self.create_user(username='user3')

    def test_proper_PostRevision_manager_is_used(self):
        "Makes sure that both normal and related managers for PostRevision don't implement .create() method"
        question = self.post_question(user=self.u1)
        self.assertRaises(NotImplementedError, question.revisions.create)
        self.assertRaises(NotImplementedError, PostRevision.objects.create)

class ContentConvertionTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u1.set_password('password')
        self.u1.set_admin_status()
        self.u1.save()
        self.u2 = self.create_user(username='notadmin')
        self.client = Client()

        #content
        self.question = self.post_question(user=self.u1)
        self.answer_to_convert = self.post_answer(user=self.u2,
                                                  question=self.question)
        self.comment_on_answer = self.post_comment(user=self.u1,
                                                   parent_post=self.answer_to_convert)
        self.another_answer = self.post_answer(user=self.u1,
                                               question=self.question)
        self.comment_to_convert = self.post_comment(user=self.u1,
                                                    parent_post=self.another_answer)

    def test_convert_comment_to_answer(self):
        self.client.login(username='user1', password='password')
        old_parent_comment_count = self.another_answer.comment_count
        answer_count = self.question.thread.answer_count
        self.client.post(reverse('comment_to_answer'),
                         {'comment_id': self.comment_to_convert.id})
        converted_answer = self.reload_object(self.comment_to_convert)
        #old_parent = self.another_answer
        old_parent = self.reload_object(self.another_answer)

        #test for convertion
        self.assertEquals(converted_answer.post_type, 'answer')
        #test for parent change
        self.assertNotEquals(old_parent.id, converted_answer.parent.id)
        #test for answer count update
        self.assertEquals(converted_answer.thread.answer_count, answer_count + 1)
        #test for comment count update
        self.assertEquals(old_parent.comment_count, old_parent_comment_count - 1)

        #test the delete post view for errors
        response = self.client.post(reverse('delete_post'),
                                    {'post_id': converted_answer.id,
                                     'cancel_vote': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue('is_deleted' in response.content)

    def test_convert_answer_to_comment(self):
        comment_count = self.question.comment_count
        #because the answer itself has a comment too!
        comment_count += self.answer_to_convert.comment_count

        answer_count = self.question.thread.answer_count
        self.client.login(username='user1', password='password')
        self.client.post(reverse('answer_to_comment'),
                         {'answer_id': self.answer_to_convert.id})
        converted_comment = self.reload_object(self.answer_to_convert)
        old_parent = self.reload_object(self.question)

        #test for convertion
        self.assertEquals(converted_comment.post_type, 'comment')
        #test for answer count update
        self.assertEquals(converted_comment.thread.answer_count, answer_count - 1)
        #test for comment count update
        self.assertEquals(old_parent.comment_count, comment_count + 1)

        #test the delete comment view for errors
        response = self.client.post(reverse('delete_comment'),
                                    {'comment_id': converted_comment.id},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
