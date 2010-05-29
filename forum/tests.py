from django.test import Client, TestCase
from django.contrib.auth.models import User
from forum import models
import datetime
from django.core.urlresolvers import reverse

class AnonymousVisitorTests(TestCase):
    fixtures = ['forum/fixtures/dump1.json',]

    def test_index(self):
        print 'trying to reverse index'
        response = self.client.get(reverse('index'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.failUnless(len(response.redirect_chain) == 1)
        self.failUnless(response.redirect_chain[0][0].endswith('/questions/'))
        c = response.context[0]
        t = response.template[0]
        self.assertEqual(t.name, 'questions.html')
        print 'index works'

    def test_reader_urls(self):
        def try_url(url_name, status_code, template = None, kwargs={}):
            url = reverse(url_name, kwargs = kwargs)
            print 'getting url %s' % url
            r = self.client.get(url)
            self.assertEqual(r.status_code, status_code)
            if template:
                #asuming that there is more than one template
                self.assertEqual(r.template[0].name, template)
        print 'entering try urls'
        try_url('sitemap', 200)
        try_url('about', 200, template='about.html')
        try_url('privacy', 200, template='privacy.html')
        try_url('logout', 200, template='logout.html')
        try_url('user_signin', 200, template='authopenid/signin.html')
        try_url(
                'answer_revisions', 
                200, 
                template='revisions_answer.html',
                kwargs={'id':38}
            )
        print 'urls are fine'

