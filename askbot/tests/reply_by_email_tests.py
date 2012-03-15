from django.utils.translation import ugettext as _
from askbot.models import ReplyAddress
from askbot.lamson_handlers import PROCESS


from askbot.tests.utils import AskbotTestCase
from askbot.models import Post, PostRevision

class MockMessage(object):

    def __init__(self, body, from_email):
        self._body = body
        self.From= from_email

    def body(self):
        return self._body

    def walk(self):
        """todo: add real file attachment"""
        return list()

class EmailProcessingTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u1.set_status('a')
        self.u1.email = "user1@domain.com"
        self.u1.save()

        self.u1.moderate_user_reputation(self.u1, reputation_change = 100, comment=  "no comment")
        self.u2 = self.create_user(username='user2')
        self.u1.moderate_user_reputation(self.u2, reputation_change = 100, comment=  "no comment")
        self.u3 = self.create_user(username='user3')
        self.u1.moderate_user_reputation(self.u3, reputation_change = 100, comment=  "no comment")

        self.question = self.post_question(
            user = self.u1,
            follow = True,
        )
        self.answer = self.post_answer(
            user = self.u2,
            question = self.question
        )

        self.comment = self.post_comment(user = self.u2, parent_post = self.answer)

    def test_process_correct_answer_comment(self):
        addr = ReplyAddress.objects.create_new( self.answer, self.u1).address
        separator = _("======= Reply above this line. ====-=-=")
        msg = MockMessage("This is a test reply \n\nOn such and such someone\
            wrote something \n\n%s\nlorem ipsum "%(separator), "user1@domain.com")
        PROCESS(msg, addr, '')
        self.assertEquals(self.answer.comments.count(), 2)
        self.assertEquals(self.answer.comments.all().order_by('-pk')[0].text.strip(), "This is a test reply")



class ReplyAddressModelTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u1.set_status('a')
        self.u1.moderate_user_reputation(self.u1, reputation_change = 100, comment=  "no comment")
        self.u2 = self.create_user(username='user2')
        self.u1.moderate_user_reputation(self.u2, reputation_change = 100, comment=  "no comment")
        self.u3 = self.create_user(username='user3')
        self.u1.moderate_user_reputation(self.u3, reputation_change = 100, comment=  "no comment")

        self.question = self.post_question(
            user = self.u1,
            follow = True,
        )
        self.answer = self.post_answer(
            user = self.u2,
            question = self.question
        )

        self.comment = self.post_comment(user = self.u2, parent_post = self.answer)
    
    def test_address_creation(self):
        self.assertEquals(ReplyAddress.objects.all().count(), 0)
        result = ReplyAddress.objects.create_new( self.answer, self.u1)
        self.assertTrue(len(result.address) >= 12 and len(result.address) <= 25)
        self.assertEquals(ReplyAddress.objects.all().count(), 1)


    def test_create_answer_reply(self):
        result = ReplyAddress.objects.create_new( self.answer, self.u1)
        post = result.create_reply("A test post")
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, "A test post")
        self.assertEquals(self.answer.comments.count(), 2)

    def test_create_comment_reply(self):
        result = ReplyAddress.objects.create_new( self.comment, self.u1)
        post = result.create_reply("A test reply")
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, "A test reply")
        self.assertEquals(self.answer.comments.count(), 2)
        

    def test_create_question_comment_reply(self):
        result = ReplyAddress.objects.create_new( self.question, self.u3)
        post = result.create_reply("A test post")
        self.assertEquals(post.post_type, "comment")
        self.assertEquals(post.text, "A test post")

    def test_create_question_answer_reply(self):
        result = ReplyAddress.objects.create_new( self.question, self.u3)
        post = result.create_reply("A test post "* 10)
        self.assertEquals(post.post_type, "answer")
        self.assertEquals(post.text, "A test post "* 10)


    

