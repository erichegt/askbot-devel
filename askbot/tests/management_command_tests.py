from django.core import management
from django.contrib import auth
from askbot.tests.utils import AskbotTestCase
from askbot import models

class ManagementCommandTests(AskbotTestCase):
    def test_add_askbot_user(self):
        username = 'test user'
        password = 'secretno1'
        management.call_command(
                        'add_askbot_user',
                        email = 'test@askbot.org',
                        username = username,
                        frequency = 'd',
                        password = password
                     )
        #check that we have the user
        users = models.User.objects.filter(username = username)
        self.assertEquals(users.count(), 1)
        user = users[0]
        #check thath subscrptions are correct
        subs = models.EmailFeedSetting.objects.filter(
                                                subscriber = user,
                                                frequency = 'd'
                                            )
        self.assertEquals(subs.count(), 5)
        #try to log in
        user = auth.authenticate(username = username, password = password)
        self.assertTrue(user is not None)
