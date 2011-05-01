from askbot.tests.utils import AskbotTestCase

class UserFollowTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user('user1')
        self.u2 = self.create_user('user2')
        self.u3 = self.create_user('user3')

    def test_user_follow(self):
        
        self.u1.follow(self.u2)
        self.u1.follow(self.u3)
        self.u2.follow(self.u1)

        self.assertEquals(
            set(self.u1.followers()),
            set([self.u2])
        )

        self.assertEquals(
            set(self.u1.
        )
