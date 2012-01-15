from askbot.models import ReplyAddress

from askbot.tests.utils import AskbotTestCase
from askbot.models import Post, PostRevision


class ReplyAddressModelTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u2 = self.create_user(username='user2')
        self.question = self.post_question(
            user = self.u1,
            follow = True,
        )
        self.answer = self.post_answer(
            user = self.u2,
            question = self.question
        )
    
    def test_creation(self):
        self.assertEquals(ReplyAddress.objects.all().count(), 0)
        result = ReplyAddress.objects.create_new( self.answer, self.u1)
        self.assertTrue(len(result.address) >= 12 and len(result.address) <= 25)
        self.assertEquals(ReplyAddress.objects.all().count(), 1)

