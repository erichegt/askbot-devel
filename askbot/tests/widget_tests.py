from datetime import datetime

from askbot import models
from askbot.tests.utils import AskbotTestCase

from django.test.client import Client
from django.core.urlresolvers import reverse


class WidgetViewsTests(AskbotTestCase):

    def setUp(self):
        self.client = Client()
        self.user = self.create_user('user1')
        self.user.set_password('sample')
        self.user.save()
        self.good_data = {'title': 'This is a title question',
                          'ask_anonymously': False}

    def test_post_with_auth(self):
        self.client.login(username='user1', password='sample')
        response = self.client.post(reverse('ask_by_widget'), self.good_data)
        self.assertEquals(response.status_code, 302)
        self.client.logout()

    def test_post_without_auth(self):
        response = self.client.post(reverse('ask_by_widget'), self.good_data)
        self.assertEquals(response.status_code, 302)
        self.assertTrue('widget_question' in self.client.session)
        self.assertEquals(self.client.session['widget_question']['title'],
                          self.good_data['title'])

    def test_post_after_login(self):
        widget_question_data = { 'title': 'testing post after login, does it?',
                                 'author': self.user,
                                 'added_at': datetime.now(),
                                 'wiki': False,
                                 'text': ' ',
                                 'tagnames': '',
                                 'is_anonymous': False
                               }

        self.client.login(username='user1', password='sample')

        session = self.client.session
        session['widget_question'] = widget_question_data
        session.save()
        response = self.client.get(reverse('ask_by_widget'),
                                   {'action': 'post-after-login'})
        self.assertFalse('widget_question' in self.client.session)
        self.assertEquals(response.status_code, 302)
        #verify posting question

class WidgetLoginViewTest(AskbotTestCase):

    def test_correct_template_loading(self):
        client = Client()
        response = client.get(reverse('widget_signin'))
        template_name = 'authopenid/widget_signin.html'
        templates = [template.name for template in response.templates]
        self.assertTrue(template_name in templates)
