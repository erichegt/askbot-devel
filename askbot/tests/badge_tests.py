from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings
from askbot import models

class BadgeTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username = 'user1')

    def assert_have_badge(self, badge_key):
        count = models.Award.objects.filter(badge__slug = badge_key).count()
        self.assertEquals(count, 1)

    def test_disciplined_badge(self):
        question = self.post_question(user = self.u1)
        question.score = settings.DISCIPLINED_BADGE_MIN_UPVOTES
        question.save()
        self.u1.delete_question(question)
        self.assert_have_badge('disciplined')

    def test_peer_pressure_badge(self):
        question = self.post_question(user = self.u1)
        answer = self.post_answer(user = self.u1, question = question)
        answer.score = -1*settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES
        answer.save()
        self.u1.delete_answer(answer)
        self.assert_have_badge('peer-pressure')
