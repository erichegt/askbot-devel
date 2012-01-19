import datetime
from operator import attrgetter
from askbot.search.state_manager import SearchState
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError
from askbot.tests.utils import AskbotTestCase
from askbot.models import Post, PostRevision, Thread, Tag


class PostModelTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u2 = self.create_user(username='user2')
        self.u3 = self.create_user(username='user3')

    def test_model_validation(self):
        self.assertRaises(
            NotImplementedError,
            PostRevision.objects.create,
            [],
            {
                'text': 'blah',
                'author': self.u1,
                'revised_at': datetime.datetime.now(),
                'revision_type': PostRevision.QUESTION_REVISION
            }
        )

        self.assertRaisesRegexp(
            AttributeError,
            r"'NoneType' object has no attribute 'revisions'",
            # cannot set `revision` without a parent
            PostRevision.objects.create_answer_revision,
            *[],
            **{
                'text': 'blah',
                'author': self.u1,
                'revised_at': datetime.datetime.now()
            }
        )

        post_revision = PostRevision(
            text='blah',
            author=self.u1,
            revised_at=datetime.datetime.now(),
            revision=1,
            revision_type=4
        )

        self.assertRaisesRegexp(
            ValidationError,
            r"{'__all__': \[u'Post field has to be set.'\], 'revision_type': \[u'Value 4 is not a valid choice.'\]}",
            post_revision.save
        )

            # revision_type not in (1,2)

        question = self.post_question(user=self.u1)

        rev2 = PostRevision(post=question, text='blah', author=self.u1, revised_at=datetime.datetime.now(), revision=2, revision_type=PostRevision.QUESTION_REVISION)
        rev2.save()
        self.assertFalse(rev2.id is None)

        post_revision = PostRevision(
            post=question,
            text='blah',
            author=self.u1,
            revised_at=datetime.datetime.now(),
            revision=2,
            revision_type=PostRevision.ANSWER_REVISION
        )
        self.assertRaisesRegexp(
            ValidationError,
            r"{'__all__': \[u'Revision_type doesn`t match values in question/answer fields.', u'Post revision with this Post and Revision already exists.'\]}",
            post_revision.save
        )


        post_revision = PostRevision(
            post=question,
            text='blah',
            author=self.u1,
            revised_at=datetime.datetime.now(),
            revision=3,
            revision_type=PostRevision.ANSWER_REVISION
        )
        self.assertRaisesRegexp(
            ValidationError,
            r"{'__all__': \[u'Revision_type doesn`t match values in question/answer fields.'\]}",
            post_revision.save
        )

        rev3 = PostRevision.objects.create_question_revision(post=question, text='blah', author=self.u1, revised_at=datetime.datetime.now(), revision_type=123) # revision_type
        self.assertFalse(rev3.id is None)
        self.assertEqual(3, rev3.revision) # By the way: let's test the auto-increase of revision number
        self.assertEqual(PostRevision.QUESTION_REVISION, rev3.revision_type)

    def test_post_revision_autoincrease(self):
        question = self.post_question(user=self.u1)
        self.assertEqual(1, question.revisions.all()[0].revision)
        self.assertEqual(1, question.revisions.count())

        question.apply_edit(edited_by=self.u1, text="blah2", comment="blahc2")
        self.assertEqual(2, question.revisions.all()[0].revision)
        self.assertEqual(2, question.revisions.count())

        question.apply_edit(edited_by=self.u1, text="blah3", comment="blahc3")
        self.assertEqual(3, question.revisions.all()[0].revision)
        self.assertEqual(3, question.revisions.count())

    def test_comment_ordering_by_date(self):
        self.user = self.u1
        q = self.post_question()

        c1 = self.post_comment(parent_post=q)
        c2 = q.add_comment(user=self.user, comment='blah blah')
        c3 = self.post_comment(parent_post=q)

        Post.objects.precache_comments(for_posts=[q], visitor=self.user)
        self.assertListEqual([c1, c2, c3], q._cached_comments)
        Post.objects.precache_comments(for_posts=[q], visitor=self.u2)
        self.assertListEqual([c1, c2, c3], q._cached_comments)

        c1.added_at, c3.added_at = c3.added_at, c1.added_at
        c1.save()
        c3.save()

        Post.objects.precache_comments(for_posts=[q], visitor=self.user)
        self.assertListEqual([c3, c2, c1], q._cached_comments)
        Post.objects.precache_comments(for_posts=[q], visitor=self.u2)
        self.assertListEqual([c3, c2, c1], q._cached_comments)

        del self.user

    def test_comment_precaching(self):
        self.user = self.u1
        q = self.post_question()

        c1 = self.post_comment(parent_post=q)
        c2 = q.add_comment(user=self.user, comment='blah blah')
        c3 = self.post_comment(parent_post=q)

        Post.objects.precache_comments(for_posts=[q], visitor=self.user)
        self.assertListEqual([c1, c2, c3], q._cached_comments)

        c1.added_at, c3.added_at = c3.added_at, c1.added_at
        c1.save()
        c3.save()

        Post.objects.precache_comments(for_posts=[q], visitor=self.user)
        self.assertListEqual([c3, c2, c1], q._cached_comments)

        del self.user

    def test_cached_get_absolute_url_1(self):
        th = lambda:1
        th.title = 'lala-x-lala'
        p = Post(id=3, post_type='question')
        p._thread_cache = th  # cannot assign non-Thread instance directly
        self.assertEqual('/question/3/lala-x-lala', p.get_absolute_url(thread=th))
        self.assertTrue(p._thread_cache is th)
        self.assertEqual('/question/3/lala-x-lala', p.get_absolute_url(thread=th))

    def test_cached_get_absolute_url_2(self):
        p = Post(id=3, post_type='question')
        th = lambda:1
        th.title = 'lala-x-lala'
        self.assertEqual('/question/3/lala-x-lala', p.get_absolute_url(thread=th))
        self.assertTrue(p._thread_cache is th)
        self.assertEqual('/question/3/lala-x-lala', p.get_absolute_url(thread=th))


class ThreadTagModelsTests(AskbotTestCase):

    # TODO: Use rich test data like page load test cases ?

    def setUp(self):
        self.create_user()
        user2 = self.create_user(username='user2')
        user3 = self.create_user(username='user3')
        self.q1 = self.post_question(tags='tag1 tag2 tag3')
        self.q2 = self.post_question(tags='tag3 tag4 tag5')
        self.q3 = self.post_question(tags='tag6', user=user2)
        self.q4 = self.post_question(tags='tag1 tag2 tag3 tag4 tag5 tag6', user=user3)

    def test_related_tags(self):
        tags = Tag.objects.get_related_to_search(threads=[self.q1.thread, self.q2.thread], ignored_tag_names=[])
        self.assertListEqual(['tag3', 'tag1', 'tag2', 'tag4', 'tag5'], [t.name for t in tags])
        self.assertListEqual([2, 1, 1, 1, 1], [t.local_used_count for t in tags])
        self.assertListEqual([3, 2, 2, 2, 2], [t.used_count for t in tags])

        tags = Tag.objects.get_related_to_search(threads=[self.q1.thread, self.q2.thread], ignored_tag_names=['tag3', 'tag5'])
        self.assertListEqual(['tag1', 'tag2', 'tag4'], [t.name for t in tags])
        self.assertListEqual([1, 1, 1], [t.local_used_count for t in tags])
        self.assertListEqual([2, 2, 2], [t.used_count for t in tags])

        tags = Tag.objects.get_related_to_search(threads=[self.q3.thread], ignored_tag_names=[])
        self.assertListEqual(['tag6'], [t.name for t in tags])
        self.assertListEqual([1], [t.local_used_count for t in tags])
        self.assertListEqual([2], [t.used_count for t in tags])

        tags = Tag.objects.get_related_to_search(threads=[self.q3.thread], ignored_tag_names=['tag1'])
        self.assertListEqual(['tag6'], [t.name for t in tags])
        self.assertListEqual([1], [t.local_used_count for t in tags])
        self.assertListEqual([2], [t.used_count for t in tags])

        tags = Tag.objects.get_related_to_search(threads=[self.q3.thread], ignored_tag_names=['tag6'])
        self.assertListEqual([], [t.name for t in tags])

        tags = Tag.objects.get_related_to_search(threads=[self.q1.thread, self.q2.thread, self.q4], ignored_tag_names=['tag2'])
        self.assertListEqual(['tag3', 'tag1', 'tag4', 'tag5', 'tag6'], [t.name for t in tags])
        self.assertListEqual([3, 2, 2, 2, 1], [t.local_used_count for t in tags])
        self.assertListEqual([3, 2, 2, 2, 2], [t.used_count for t in tags])

    def test_run_adv_search_1(self):
        ss = SearchState.get_empty()
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(4, qs.count())

    def test_run_adv_search_ANDing_tags(self):
        ss = SearchState.get_empty()
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss.add_tag('tag1'))
        self.assertEqual(2, qs.count())

        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss.add_tag('tag1').add_tag('tag3'))
        self.assertEqual(2, qs.count())

        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss.add_tag('tag1').add_tag('tag3').add_tag('tag6'))
        self.assertEqual(1, qs.count())

        ss = SearchState(scope=None, sort=None, query="#tag3", tags='tag1, tag6', author=None, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(1, qs.count())

    def test_run_adv_search_query_author(self):
        ss = SearchState(scope=None, sort=None, query="@user", tags=None, author=None, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(2, len(qs))
        self.assertEqual(self.q1.thread_id, min(qs[0].id, qs[1].id))
        self.assertEqual(self.q2.thread_id, max(qs[0].id, qs[1].id))

        ss = SearchState(scope=None, sort=None, query="@user2", tags=None, author=None, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(1, len(qs))
        self.assertEqual(self.q3.thread_id, qs[0].id)

        ss = SearchState(scope=None, sort=None, query="@user3", tags=None, author=None, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(1, len(qs))
        self.assertEqual(self.q4.thread_id, qs[0].id)

    def test_run_adv_search_url_author(self):
        ss = SearchState(scope=None, sort=None, query=None, tags=None, author=self.user.id, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(2, len(qs))
        self.assertEqual(self.q1.thread_id, min(qs[0].id, qs[1].id))
        self.assertEqual(self.q2.thread_id, max(qs[0].id, qs[1].id))

        ss = SearchState(scope=None, sort=None, query=None, tags=None, author=self.user2.id, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(1, len(qs))
        self.assertEqual(self.q3.thread_id, qs[0].id)

        ss = SearchState(scope=None, sort=None, query=None, tags=None, author=self.user3.id, page=None, user_logged_in=None)
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        self.assertEqual(1, len(qs))
        self.assertEqual(self.q4.thread_id, qs[0].id)

    def test_thread_caching_1(self):
        ss = SearchState.get_empty()
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        qs = list(qs)

        for thread in qs:
            self.assertIsNone(getattr(thread, '_question_cache', None))
            self.assertIsNone(getattr(thread, '_last_activity_by_cache', None))

            post = Post.objects.get(post_type='question', thread=thread.id)
            self.assertEqual(post, thread._question_post())
            self.assertEqual(post, thread._question_cache)
            self.assertTrue(thread._question_post() is thread._question_cache)

    def test_thread_caching_2_precache_view_data_hack(self):
        ss = SearchState.get_empty()
        qs, meta_data = Thread.objects.run_advanced_search(request_user=self.user, search_state=ss)
        qs = list(qs)

        Thread.objects.precache_view_data_hack(threads=qs)

        for thread in qs:
            post = Post.objects.get(post_type='question', thread=thread.id)
            self.assertEqual(post.id, thread._question_cache.id) # Cannot compare models instances with deferred model instances
            self.assertEqual(post.id, thread._question_post().id)
            self.assertTrue(thread._question_post() is thread._question_cache)

            user = User.objects.get(id=thread.last_activity_by_id)
            self.assertEqual(user.id, thread._last_activity_by_cache.id)
            self.assertTrue(thread.last_activity_by is thread._last_activity_by_cache)


