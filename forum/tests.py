from django.test import Client, TestCase
from django.contrib.auth.models import User
from forum import models
import datetime
from django.core.urlresolvers import reverse

class AnonymousVisitorTests(TestCase):
    fixtures = ['forum/fixtures/full_dump.json',]

    def test_index(self):
        #todo: merge this with all reader url tests
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
        #todo: test redirects better
        def try_url(
                url_name, status_code=200, template=None, 
                kwargs={}, redirect_url=None, follow=False
            ):
            url = reverse(url_name, kwargs = kwargs)
            print 'getting url %s' % url
            r = self.client.get(url, follow=follow)
            if hasattr(self.client, 'redirect_chain'):
                print self.client.redirect_chain
            self.assertEqual(r.status_code, status_code)
            if template:
                #asuming that there is more than one template
                self.assertEqual(r.template[0].name, template)
        try_url('sitemap')
        try_url('about', template='about.html')
        try_url('privacy', template='privacy.html')
        try_url('logout', template='logout.html')
        try_url('user_signin', template='authopenid/signin.html')
        try_url('tags', template='tags.html')
        try_url('badges', template='badges.html')
        try_url(
                'answer_revisions', 
                template='revisions_answer.html',
                kwargs={'id':38}
            )
        try_url(
                'questions',
                template='questions.html'
            )
        try_url(
                'question',
                kwargs={'id':1},
            )
        try_url(
                'question',
                kwargs={'id':2},
            )
        try_url(
                'question',
                kwargs={'id':3},
            )
        try_url(
                'question_revisions',
                kwargs={'id':17},
                template='revisions_question.html'
            )
        try_url(
                'users',
                template='users.html'
            )
        try_url(
                'edit_user',
                template='authopenid/signin.html',
                kwargs={'id':4},
                status_code=200,
                follow=True,
            )
