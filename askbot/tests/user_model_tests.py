from askbot.tests.utils import AskbotTestCase
from django.contrib.auth.models import User
from askbot import models
from askbot.models.tag import format_personal_group_name

class UserModelTests(AskbotTestCase):
    """test user model"""

    def test_new_user_has_personal_group(self):
        user = User.objects.create_user('somebody', 'somebody@example.com')
        group_name = format_personal_group_name(user)
        group = models.Group.objects.filter(name=group_name)
        self.assertEqual(group.count(), 1)
        memberships = models.GroupMembership.objects.filter(
                                                group=group, user=user
                                            )
        self.assertEqual(memberships.count(), 1)
