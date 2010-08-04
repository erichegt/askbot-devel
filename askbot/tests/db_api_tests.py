"""Tests database api - the basic data entry 
functions that happen on behalf of users

e.g. ``some_user.do_something(...)``
"""
from askbot.tests.utils import AskbotTestCase

class DBApiTests(AskbotTestCase):

    def test_flag_question(self):
        self.create_user()
        question = self.post_question()
        self.user.set_status('m')
        self.user.flag_post(question)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )

    def test_flag_answer(self):
        self.create_user()
        question = self.post_question()
        answer = self.post_answer(question = question)
        self.user.set_status('m')
        self.user.flag_post(answer)
        self.assertEquals(
            len(self.user.flaggeditems.all()),
            1
        )
