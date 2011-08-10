from django.conf import settings as django_settings
from askbot.tests.utils import AskbotTestCase
from askbot.utils import markup

class MarkupTest(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user('user1')

    def test_mentionize_text(self):
        '''this test also test implicitly 
        test extract_first_matching_mentioned_author'''
        text = "oh hai @user1 how are you? @UsEr1"
        expected_output = 'oh hai <a href="%(user_url)s">@user1</a> how are you?'
        expected_output += ' <a href="%(user_url)s">@user1</a>'
        anticipated_authors = [self.u1,]
        mentioned_authors, output = markup.mentionize_text(text, anticipated_authors)
        self.assertTrue(self.u1 in mentioned_authors)
        self.assertEquals(output, expected_output % {'user_url': self.u1.get_profile_url()}) 

    def test_extract_mentioned_name_seeds(self):
        text = "oh hai @user1 how are you?"
        output = markup.extract_mentioned_name_seeds(text)
        self.assertEquals(output, set(['user1']))
