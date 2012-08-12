from datetime import datetime

from askbot import models
from askbot.tests.utils import AskbotTestCase

from django.test.client import Client
from django.core.urlresolvers import reverse


class WidgetViewsTests(AskbotTestCase):

    def setUp(self):
        self.client = Client()
        self.widget = models.AskWidget.objects.create(title='foo widget')
        self.user = self.create_user('user1')
        self.user.set_password('sample')
        self.user.save()
        self.good_data = {'title': 'This is a title question',
                          'ask_anonymously': False}

    def test_post_with_auth(self):
        self.client.login(username='user1', password='sample')
        response = self.client.post(reverse('ask_by_widget', args=(self.widget.id, )), self.good_data)
        self.assertEquals(response.status_code, 302)
        self.client.logout()

    def test_post_without_auth(self):
        #weird issue
        response = self.client.post(reverse('ask_by_widget', args=(self.widget.id, )), self.good_data)
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
        response = self.client.get(reverse('ask_by_widget', args=(self.widget.id, )),
                                   {'action': 'post-after-login'})
        self.assertFalse('widget_question' in self.client.session)
        self.assertEquals(response.status_code, 302)
        #verify posting question

    def test_render_widget_view(self):
        response = self.client.get(reverse('render_ask_widget', args=(self.widget.id, )))
        self.assertEquals(200, response.status_code)
        mimetype = 'text/javascript'
        self.assertTrue(mimetype in response['Content-Type'])


class WidgetLoginViewTest(AskbotTestCase):

    def test_correct_template_loading(self):
        client = Client()
        response = client.get(reverse('widget_signin'))
        template_name = 'authopenid/widget_signin.html'
        templates = [template.name for template in response.templates]
        self.assertTrue(template_name in templates)

class WidgetCreatorViewsTests(AskbotTestCase):

    def setUp(self):
        self.client = Client()
        self.user = self.create_user('user1')
        self.user.set_password('testpass')
        self.user.set_admin_status()
        self.user.save()

    def test_list_ask_widget_view(self):
        self.client.login(username='user1', password='testpass')
        response = self.client.get(reverse('list_ask_widgets'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('widgets' in response.context)

    def test_create_ask_widget_get(self):
        self.client.login(username='user1', password='testpass')
        response = self.client.get(reverse('create_ask_widget'))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('form' in response.context)

    def test_create_ask_widget_post(self):
        self.client.login(username='user1', password='testpass')
        post_data = {'title': 'Test widget'}
        response = self.client.post(reverse('create_ask_widget'), post_data)
        self.assertEquals(response.status_code, 302)
