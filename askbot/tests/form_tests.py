from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings as askbot_settings
from askbot import forms
from askbot import models

class TagNamesFieldTests(AskbotTestCase):

    def setUp(self):
        self.field = forms.TagNamesField()
        self.user = self.create_user('user1')

    def clean(self, value):
        return self.field.clean(value).strip().split(' ')

    def assert_tags_equal(self, tag_list1, tag_list2):
        self.assertEqual(sorted(tag_list1), sorted(tag_list2))

    def test_force_lowercase(self):
        """FORCE_LOWERCASE setting is on
        """
        askbot_settings.update('FORCE_LOWERCASE_TAGS', True)
        cleaned_tags = self.clean('Tag1 TAG5 tag1 tag5')
        self.assert_tags_equal(cleaned_tags, ['tag1','tag5'])

    def test_custom_case(self):
        """FORCE_LOWERCASE setting is off
        """
        askbot_settings.update('FORCE_LOWERCASE_TAGS', False)
        models.Tag(name = 'TAG1', created_by = self.user).save()
        models.Tag(name = 'Tag2', created_by = self.user).save()
        cleaned_tags = self.clean('tag1 taG2 TAG1 tag3 tag3')
        self.assert_tags_equal(cleaned_tags, ['TAG1', 'Tag2', 'tag3'])



