import datetime
import time
from django.test import TestCase
from django.template import defaultfilters
from django.core.urlresolvers import reverse
from askbot.models import User, Question, Answer, Activity
from askbot.models import EmailFeedSetting
from askbot import const

def create_user(username = None, email = None):
    user = User.objects.create_user(username, email)
    for feed_type in EmailFeedSetting.FEED_TYPES:
        feed = EmailFeedSetting(
                        feed_type = feed_type[0],
                        frequency = 'n',
                        subscriber = user
                    )
        feed.save()
    return user

def get_re_notif_after(timestamp):
    notifications = Activity.objects.filter(
            activity_type__in = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY,
            active_at__gte = timestamp
        )
    return notifications

class UpdateNotificationTests(TestCase):

    def reset_response_counts(self):
        self.reload_users()
        for user in self.users:
            user.response_count = 0
            user.save()

    def reload_users(self):
        self.u11 = User.objects.get(id=self.u11.id)
        self.u12 = User.objects.get(id=self.u12.id)
        self.u13 = User.objects.get(id=self.u13.id)
        self.u14 = User.objects.get(id=self.u14.id)
        self.u21 = User.objects.get(id=self.u21.id)
        self.u22 = User.objects.get(id=self.u22.id)
        self.u23 = User.objects.get(id=self.u23.id)
        self.u24 = User.objects.get(id=self.u24.id)
        self.u31 = User.objects.get(id=self.u31.id)
        self.u32 = User.objects.get(id=self.u32.id)
        self.u33 = User.objects.get(id=self.u33.id)
        self.u34 = User.objects.get(id=self.u34.id)
        self.users = [
            self.u11,
            self.u12,
            self.u13,
            self.u14,
            self.u21,
            self.u22,
            self.u23,
            self.u24,
            self.u31,
            self.u32,
            self.u33,
            self.u34,
        ]

    def setUp(self):
        #users for the question
        self.u11 = create_user('user11', 'user11@example.com')
        self.u12 = create_user('user12', 'user12@example.com')
        self.u13 = create_user('user13', 'user13@example.com')
        self.u14 = create_user('user14', 'user14@example.com')

        #users for first answer
        self.u21 = create_user('user21', 'user21@example.com')#post answer
        self.u22 = create_user('user22', 'user22@example.com')#edit answer
        self.u23 = create_user('user23', 'user23@example.com')
        self.u24 = create_user('user24', 'user24@example.com')

        #users for second answer
        self.u31 = create_user('user31', 'user31@example.com')#post answer
        self.u32 = create_user('user32', 'user32@example.com')#edit answer
        self.u33 = create_user('user33', 'user33@example.com')
        self.u34 = create_user('user34', 'user34@example.com')

        #a hack to initialize .users list
        self.reload_users()

        #pre-populate askbot with some content
        self.question = Question.objects.create_new(
                            title = 'test question',
                            author = self.u11,
                            added_at = datetime.datetime.now(),
                            wiki = False,
                            tagnames = 'test', 
                            text = 'hey listen up',
                        )
        self.comment12 = self.question.add_comment(
                            user = self.u12,
                            comment = 'comment12'
                        )
        self.comment13 = self.question.add_comment(
                            user = self.u13,
                            comment = 'comment13'
                        )
        self.answer1 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u21,
                            added_at = datetime.datetime.now(),
                            text = 'answer1'
                        )
        self.comment22 = self.answer1.add_comment(
                            user = self.u22,
                            comment = 'comment22'
                        )
        self.comment23 = self.answer1.add_comment(
                            user = self.u23,
                            comment = 'comment23'
                        )
        self.answer2 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u31,
                            added_at = datetime.datetime.now(),
                            text = 'answer2'
                        )
        self.comment32 = self.answer2.add_comment(
                            user = self.u32,
                            comment = 'comment32'
                        )
        self.comment33 = self.answer2.add_comment(
                            user = self.u33,
                            comment = 'comment33'
                        )

    def test_self_comments(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u21,
                            comment = 'self-comment 2',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u22, self.u23]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 1, 1, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_question1(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment @user11',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_question2(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u11,
                            comment = 'self-comment @user11 blah',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u12, self.u13]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_self_mention_not_posting_in_comment_to_answer(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u21,
                            comment = 'self-comment 1 @user21',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u22, self.u23]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 0, 1, 1, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_comments_to_post_authors(self):
        self.question.apply_edit(
                        edited_by = self.u14,
                        text = 'now much better',
                        comment = 'improved text'
                    )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.add_comment(
                            user = self.u12,
                            comment = 'self-comment 1',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u13, self.u14]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 0, 1, 1,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )
        self.answer1.apply_edit(
                        edited_by = self.u24,
                        text = 'now much better',
                        comment = 'improved text'
                    )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.add_comment(
                            user = self.u22,
                            comment = 'self-comment 1',
                            added_at = timestamp
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u21, self.u23, self.u24]),
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 0, 0, 0,
                 1, 0, 1, 1,
                 0, 0, 0, 0,
            ]
        )

    def test_question_edit(self):
        """when question is edited
        response receivers are question authors, commenters
        and answer authors, but not answer commenters
        """
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.apply_edit(
                        edited_by = self.u14,
                        text = 'waaay better question!',
                        comment = 'improved question',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u12, self.u13, self.u21, self.u31])
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 0, 0, 0,
                 1, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.question.apply_edit(
                        edited_by = self.u31,
                        text = 'waaay even better question!',
                        comment = 'improved question',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set([self.u11, self.u12, self.u13, self.u14, self.u21])
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 1,
                 1, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )

    def test_answer_edit(self):
        """
        """
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer1.apply_edit(
                        edited_by = self.u24,
                        text = 'waaay better answer!',
                        comment = 'improved answer1',
                    )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u11, self.u12, self.u13, 
                    self.u21, self.u22, self.u23,
                    self.u31
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 1, 1, 0,
                 1, 0, 0, 0,
            ]
        )

    def test_new_answer(self):
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer3 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u11,
                            added_at = timestamp,
                            text = 'answer3'
                        )
        time_end = datetime.datetime.now()
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u12, self.u13, 
                    self.u21, self.u31
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 0, 1, 1, 0,
                 1, 0, 0, 0,
                 1, 0, 0, 0,
            ]
        )
        self.reset_response_counts()
        time.sleep(1)
        timestamp = datetime.datetime.now()
        self.answer3 = Answer.objects.create_new(
                            question = self.question,
                            author = self.u31,
                            added_at = timestamp,
                            text = 'answer4'
                        )
        notifications = get_re_notif_after(timestamp)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(
            set(notifications[0].receiving_users.all()),
            set(
                [
                    self.u11, self.u12, self.u13, 
                    self.u21
                ]
            )
        )
        self.reload_users()
        self.assertEqual(
            [
                self.u11.response_count,
                self.u12.response_count,
                self.u13.response_count,
                self.u14.response_count,
                self.u21.response_count,
                self.u22.response_count,
                self.u23.response_count,
                self.u24.response_count,
                self.u31.response_count,
                self.u32.response_count,
                self.u33.response_count,
                self.u34.response_count,
            ],
            [
                 1, 1, 1, 0,
                 1, 0, 0, 0,
                 0, 0, 0, 0,
            ]
        )


class AnonymousVisitorTests(TestCase):
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

    def test_reader_urls(self):
        """test all reader views thoroughly
        on non-crashiness (no correcteness tests here)
        """

        def try_url(
                url_name, status_code=200, template=None, 
                kwargs={}, redirect_url=None, follow=False,
                data = {}
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

        try_url('sitemap')
        try_url('about', template='about.html')
        try_url('privacy', template='privacy.html')
        try_url('logout', template='logout.html')
        try_url('user_signin', template='authopenid/signin.html')
        #todo: test different tabs
        try_url('tags', template='tags.html')
        try_url('tags', data={'sort':'name'}, template='tags.html')
        try_url('tags', data={'sort':'used'}, template='tags.html')
        try_url('badges', template='badges.html')
        try_url(
                'answer_revisions', 
                template='revisions_answer.html',
                kwargs={'id':38}
            )
        #todo: test different sort methods and scopes
        try_url(
                'questions',
                template='questions.html'
            )
        try_url(
                'questions',
                data={'start_over':'true'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'all'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'favorite'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'latest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'oldest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'active'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'scope':'unanswered', 'sort':'inactive'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'hottest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'coldest'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'mostvoted'},
                template='questions.html'
            )
        try_url(
                'questions',
                data={'sort':'leastvoted'},
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
        try_url('users', template='users.html')
        #todo: really odd naming conventions for sort methods
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user'},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':2},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'reputation', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'newest', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'last', 'page':1},
            )
        try_url(
                'users',
                template='users.html',
                data={'sort':'user', 'page':1},
            )
        try_url(
                'edit_user',
                template='authopenid/signin.html',
                kwargs={'id':4},
                status_code=200,
                follow=True,
            )
        user = User.objects.get(id=2)
        name_slug = defaultfilters.slugify(user.username)
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'stats'}, 
            template='user_stats.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'recent'}, 
            template='user_recent.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'responses'}, 
            status_code=404,
            template='404.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'reputation'}, 
            template='user_reputation.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'votes'}, 
            status_code=404,
            template='404.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'favorites'}, 
            template='user_favorites.html'
        )
        try_url(
            'user_profile', 
            kwargs={'id': 2, 'slug': name_slug},
            data={'sort':'email_subscriptions'}, 
            status_code=404,
            template='404.html'
        )
