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

"""collection of quote separators separated with an empty line
u'\n\nthis is my reply!\n\nOn Wed, Oct 31, 2012 at 1:45 AM, <kp@kp-dev.askbot.com> wrote:\n\n> **\n>            '

u'\n\nthis is my another reply!\n\nOn Wed, Oct 31, 2012 at 1:45 AM, <kp@kp-dev.askbot.com> wrote:\n>\n> '

u'\n\nSending this from my yahoo mail account.\n\n\n\n________________________________\n From: "kp@kp-dev.askbot.com" <kp@kp-dev.askbot.com>\nTo: fadeev@rocketmail.com \nSent: Wednesday, October 31, 2012 2:41 AM\nSubject: "This is my test question"\n \n\n  \n \n \n'

u'On Monday 01 October 2012 21:22:44 you wrote: \n\nSecond try, no HTML kmail does weird things.'

u'outlook.com (new hotmail) with RTF on \n\nSubject: "Posting a question by email." \nFrom: kp@kp-dev.askbot.com \nTo: aj_fitoria@hotmail.com \nDate: Thu, 1 Nov 2012 16:30:27 +0000'

u'reply from hotmail without RTF \n________________________________ \n> Subject: "test with recovered signature" \n> From: kp@kp-dev.askbot.com \n> To: aj_fitoria@hotmail.com \n> Date: Thu, 1 Nov 2012 16:44:35 +0000'

"""
