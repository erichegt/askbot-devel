from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings as askbot_settings
from askbot import models
import django.core.mail

class ThreadModelTestsWithGroupsEnabled(AskbotTestCase):
    
    def setUp(self):
        self.groups_enabled_backup = askbot_settings.GROUPS_ENABLED
        askbot_settings.update('GROUPS_ENABLED', True)
        self.admin = self.create_user('admin', status = 'd')
        self.user = self.create_user(
            'user',
            notification_schedule = {
                'q_ask': 'i',
                'q_all': 'i',
                'q_ans': 'i',
                'q_sel': 'i',
                'm_and_c': 'i'
            }
        )
        self.group = models.Tag.group_tags.get_or_create(
            group_name = 'jockeys', user = self.admin
        )
        self.admin.edit_group_membership(
            group = self.group,
            user = self.admin,
            action = 'add'
        )

    def tearDown(self):
        askbot_settings.update('GROUPS_ENABLED', self.groups_enabled_backup)

    def test_private_answer(self):
        # post question, answer, add answer to the group
        self.question = self.post_question(self.user)

        self.answer = self.post_answer(
            user = self.admin,
            question = self.question,
            is_private = True
        )

        thread = self.question.thread

        #test answer counts
        self.assertEqual(thread.get_answer_count(self.user), 0)
        self.assertEqual(thread.get_answer_count(self.admin), 1)

        #test mail outbox
        self.assertEqual(len(django.core.mail.outbox), 0)
        user = self.reload_object(self.user)
        self.assertEqual(user.new_response_count, 0)

        self.admin.edit_answer(
            self.answer,
            is_private = False
        )
        self.assertEqual(len(django.core.mail.outbox), 1)
        user = self.reload_object(self.user)
        self.assertEqual(user.new_response_count, 1)
