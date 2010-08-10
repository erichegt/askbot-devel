"""Tests database api - the basic data entry 
functions that happen on behalf of users

e.g. ``some_user.do_something(...)``
"""
from askbot.tests.utils import AskbotTestCase

class DBApiTests(AskbotTestCase):

    def setUp(self):
        self.create_user()
        self.create_user(username = 'other_user')
        self.question = self.post_question()

    def test_flag_question(self):
        self.user.set_status('m')
        self.user.flag_post(self.question)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )

    def test_flag_answer(self):
        answer = self.post_answer(question = self.question)
        self.user.set_status('m')
        self.user.flag_post(answer)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )

    def test_accept_best_answer(self):
        answer = self.post_answer(
                            question = self.question,
                            user = self.other_user
                        )
        self.user.accept_best_answer(answer)
