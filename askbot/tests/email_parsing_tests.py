from django.conf import settings as django_settings
from askbot.skins.loaders import get_template
from django.template import Context
from askbot import mail
from askbot import models
from askbot.tests import utils

class EmailParseTests(utils.AskbotTestCase):

    def setUp(self):
        self.template_name = 'email/welcome_lamson_on.html'
        self.context = {'site_name': 'askbot.com',
                        'email_code': 'DwFwndQty'}
        template = get_template(self.template_name)
        self.rendered_template = template.render(Context(self.context))
        self.expected_output = 'Welcome to askbot.com!\n\nImportant: Please reply to this message, without editing it. We need this to determine your email signature and that the email address is valid and was typed correctly.\n\nUntil we receive the response from you, you will not be able ask or answer questions on askbot.com by email.\n\nSincerely,askbot.com Administrator\n\nDwFwndQty'

    def test_clean_email_body(self):
        cleaned_body = mail.clean_html_email(self.rendered_template)
        print "EXPECTED BODY"
        print self.expected_output
        print '=================================================='
        print cleaned_body
        print "CLEANED BODY"
        self.assertEquals(cleaned_body, self.expected_output)
