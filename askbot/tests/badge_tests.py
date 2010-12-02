from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings
from askbot import models

class BadgeTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username = 'user1')
        self.u2 = self.create_user(username = 'user2')
        self.u3 = self.create_user(username = 'user3')

    def assert_have_badge(self, badge_key, expected_count = 1):
        count = models.Award.objects.filter(badge__slug = badge_key).count()
        self.assertEquals(count, expected_count)

    def assert_voted_answer_badge_works(self, 
                                    badge_key = None,
                                    min_score = None,
                                    multiple = False
                                ):
        """test answer badge where answer author
        where badge award is triggered by upvotes
        * min_score - minimum # of upvotes required
        * multiple - multiple award or not
        * badge_key - key on askbot.models.badges.Badge object
        """
        question = self.post_question(user = self.u1)
        answer = self.post_answer(user = self.u2, question = question)
        answer.score = min_score
        answer.save()
        self.u1.upvote(answer)
        self.assert_have_badge(badge_key)
        self.u3.upvote(answer)
        self.assert_have_badge(badge_key, expected_count = 1)
        
        #post another question and check that there are no new badges
        answer2 = self.post_answer(user = self.u2, question = question)
        answer2.score = min_score
        answer2.save()
        self.u1.upvote(answer2)

        if multiple == True:
            expected_count = 2
        else:
            expected_count = 1

        self.assert_have_badge(badge_key, expected_count = expected_count)

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

    def test_teacher_badge(self):
        self.assert_voted_answer_badge_works(
            badge_key = 'teacher',
            min_score = settings.TEACHER_BADGE_MIN_UPVOTES,
            multiple = False
        )

    def test_nice_answer_badge(self):
        self.assert_voted_answer_badge_works(
            badge_key = 'nice-answer',
            min_score = settings.NICE_ANSWER_BADGE_MIN_UPVOTES,
            multiple = True
        )
