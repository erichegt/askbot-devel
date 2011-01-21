from django.test import TestCase, signals
from jinja2.environment import Template as Jinja2Template
from django.template import defaultfilters
from django.core.urlresolvers import reverse
import coffin.template
from askbot import models
from askbot.utils.slug import slugify
import sys

#note - this code can be run only once
ORIG_JINJA2_RENDERER = Jinja2Template.render
def instrumented_render(template_object, *args, **kwargs):
    context = dict(*args, **kwargs)
    signals.template_rendered.send(
                            sender=template_object,
                            template=template_object,
                            context=context
                        )
    return ORIG_JINJA2_RENDERER(template_object, *args, **kwargs)
Jinja2Template.render = instrumented_render

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
            if isinstance(r.template, coffin.template.Template):
                self.assertEqual(r.template.name, template)
            else:
                #asuming that there is more than one template
                template_names = ','.join([t.name for t in r.template])
                print 'templates are %s' % template_names
                self.assertEqual(r.template[0].name, template)

class PageLoadTests(PageLoadTestCase):
    fixtures = ['tmp/fixture2.json', ]

    def test_index(self):
        #todo: merge this with all reader url tests
        response = self.client.get(reverse('index'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.failUnless(len(response.redirect_chain) == 1)
        self.failUnless(response.redirect_chain[0][0].endswith('/questions/'))
        self.assertEquals(response.template.name, 'questions.html')

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
                template='revisions.html',
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
                data={'scope':'unanswered', 'sort':'age-desc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'age-asc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'activity-desc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'activity-asc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'answers-desc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'answers-asc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'votes-desc'},
                template='questions.html'
            )
        self.try_url(
                'questions',
                data={'sort':'votes-asc'},
                template='questions.html'
            )
        self.try_url(
                'question',
                kwargs={'id':1},
                follow=True,
                template='question.html'
            )
        self.try_url(
                'question',
                kwargs={'id':2},
                follow=True,
                template='question.html'
            )
        self.try_url(
                'question',
                kwargs={'id':3},
                follow=True,
                template='question.html'
            )
        self.try_url(
                'question_revisions',
                kwargs={'id':17},
                template='revisions.html'
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
        name_slug = slugify(user.username)
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'stats'}, 
            template='user_profile/user_stats.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'recent'}, 
            template='user_profile/user_recent.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'inbox'}, 
            status_code=404,
            template='404.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'reputation'}, 
            template='user_profile/user_reputation.html'
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
            template='user_profile/user_favorites.html'
        )
        self.try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'email_subscriptions'}, 
            status_code=404,
            template='404.html'
        )
