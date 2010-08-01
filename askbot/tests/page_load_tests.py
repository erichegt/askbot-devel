from django.test import TestCase
from django.template import defaultfilters
from django.core.urlresolvers import reverse
from askbot import models

class PageLoadTestCase(TestCase):
    def try_url(
            self,
            url_name, status_code=200, template=None, 
            kwargs={}, redirect_url=None, follow=False,
            data = {},
        ):
        url = reverse(url_name, kwargs = kwargs)
        url_info = 'getting url %s' % url
        if data:
            url_info += '?' + '&'.join(['%s=%s' % (k, v) for k, v in data.iteritems()])
        print url_info

        r = self.client.get(url, data=data, follow=follow)
        if hasattr(self.client, 'redirect_chain'):
            print 'redirect chain: %s' % ','.join(self.client.redirect_chain)

        self.assertEqual(r.status_code, status_code)

        if template:
            #asuming that there is more than one template
            print 'templates are %s' % ','.join([t.name for t in r.template])
            self.assertEqual(r.template[0].name, template)

class PageLoadTests(PageLoadTestCase):
    fixtures = ['tmp/fixture1.json', ]

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

    def proto_test_non_user_urls(self):
        """test all reader views thoroughly
        on non-crashiness (no correcteness tests here)
        """

        self.try_url('sitemap')
        self.try_url('feeds', kwargs={'url':'rss'})
        self.try_url('about', template='about.html')
        self.try_url('privacy', template='privacy.html')
        self.try_url('logout', template='logout.html')
        self.try_url('user_signin', template='authopenid/signin.html')
        #todo: test different tabs
        self.try_url('tags', template='tags.html')
        self.try_url('tags', data={'sort':'name'}, template='tags.html')
        self.try_url('tags', data={'sort':'used'}, template='tags.html')
        self.try_url('badges', template='badges.html')
        self.try_url(
                'answer_revisions', 
                template='revisions_answer.html',
                kwargs={'id':38}
            )
        #todo: test different sort methods and scopes
        self.try_url(
                'questions',
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'start_over':'true'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'all'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'favorite'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'latest'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'oldest'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'active'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'inactive'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'hottest'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'coldest'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'mostvoted'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'leastvoted'},
                template='questions.html'
            )
        self.try_url(
                'question',
                kwargs={'id':1},
            )
        self.try_url(
                'question',
                kwargs={'id':2},
            )
        self.try_url(
                'question',
                kwargs={'id':3},
            )
        self.try_url(
                'question_revisions',
                kwargs={'id':17},
                template='revisions_question.html'
            )
        self.try_url('users', template='users.html')
        #todo: really odd naming conventions for sort methods
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'reputation'},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'newest'},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'last'},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'user'},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':2},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':2},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':2},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':2},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':1},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':1},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':1},
            )
        self.try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':1},
            )
        self.try_url(
                'edit_user',
                template='authopenid/signin.html',
                kwargs={'id':4},
                status_code=200,
                follow=True,
            )

    def test_non_user_urls(self):
        self.proto_test_non_user_urls()

    #def test_non_user_urls_logged_in(self):
        #user = User.objects.get(id=1)
        #somehow login this user
        #self.proto_test_non_user_urls()

    def test_user_urls(self):
        user = models.User.objects.get(id=2)
        name_slug = defaultfilters.slugify(user.username)
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'stats'}, 
            template='user_stats.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'recent'}, 
            template='user_recent.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'responses'}, 
            status_code=404,
            template='404.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'reputation'}, 
            template='user_reputation.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'votes'}, 
            status_code=404,
            template='404.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'favorites'}, 
            template='user_favorites.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'email_subscriptions'}, 
            status_code=404,
            template='404.html'
        )
