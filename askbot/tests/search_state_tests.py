import re
import unittest
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from askbot.search.state_manager import SearchState, ViewLog, parse_query
from askbot import const

DEFAULT_SORT = const.DEFAULT_POST_SORT_METHOD
class SearchStateTests(TestCase):
    def setUp(self):
        self.state = SearchState()
        self.log = ViewLog()

    def visit_page(self, page_name):
        """page_name is name of the view function
        that is to be "visited"
        """
        self.log.set_current(page_name)

    def update(self, data, user = None):
        self.visit_page('questions')
        if user is None:
            user = AnonymousUser()
        self.state.update(data, self.log, user)

    def add_tag(self, tag):
        self.update({'tags': set([tag])})

    def remove_tag(self, tag):
        self.update({'remove_tag': tag})

    def assert_tags_are(self, *args):
        self.assertEqual(self.state.tags, set(args))

    def test_add_remove_tags(self):
        self.add_tag('tag1')
        self.assert_tags_are('tag1')
        self.add_tag('tag2')
        self.assert_tags_are('tag1', 'tag2')
        self.add_tag('tag3')
        self.assert_tags_are('tag1', 'tag2', 'tag3')
        self.remove_tag('tag3')
        self.assert_tags_are('tag1', 'tag2')
        self.remove_tag('tag2')
        self.assert_tags_are('tag1')
        self.remove_tag('tag1')
        self.assertEqual(len(self.state.tags), 0)

    def test_query_and_tags1(self):
        self.update({'query': 'hahaha'})
        self.add_tag('tag1')
        self.assertEquals(self.state.query, 'hahaha')
        self.assert_tags_are('tag1')
        self.update({'reset_query': True})
        self.assertEquals(self.state.query, None)
        self.assert_tags_are('tag1')

    def test_start_over(self):
        self.update({'query': 'hahaha'})
        self.add_tag('tag1')
        self.update({'start_over': True})
        self.assertEquals(self.state.query, None)
        self.assertEquals(self.state.tags, None)

    def test_auto_reset_sort(self):
        self.update({'sort': 'age-asc'})
        self.assertEquals(self.state.sort, 'age-asc')
        self.update({})
        self.assertEquals(self.state.sort, DEFAULT_SORT)
class ParseQueryTests(unittest.TestCase):
    def test_extract_users(self):
        text = '@anna haha @"maria fernanda" @\'diego maradona\' hehe [user:karl  marx] hoho  user:\' george bush  \''
        parse_results = parse_query(text)
        self.assertEquals(
            sorted(parse_results['query_users']),
            sorted(['anna', 'maria fernanda', 'diego maradona', 'karl marx', 'george bush'])
        )
        self.assertEquals(parse_results['stripped_query'], 'haha hehe hoho')

    def test_extract_tags(self):
        text = '#tag1 [tag: tag2] some text [tag3] query'
        parse_results = parse_query(text)
        self.assertEquals(set(parse_results['query_tags']), set(['tag1', 'tag2', 'tag3']))
        self.assertEquals(parse_results['stripped_query'], 'some text query')

    def test_extract_title1(self):
        text = 'some text query [title: what is this?]'
        parse_results = parse_query(text)
        self.assertEquals(parse_results['query_title'], 'what is this?')
        self.assertEquals(parse_results['stripped_query'], 'some text query')

    def test_extract_title2(self):
        text = 'some text query title:"what is this?"'
        parse_results = parse_query(text)
        self.assertEquals(parse_results['query_title'], 'what is this?')
        self.assertEquals(parse_results['stripped_query'], 'some text query')

    def test_extract_title3(self):
        text = 'some text query title:\'what is this?\''
        parse_results = parse_query(text)
        self.assertEquals(parse_results['query_title'], 'what is this?')
        self.assertEquals(parse_results['stripped_query'], 'some text query')

    def test_negative_match(self):
        text = 'some query text'
        parse_results = parse_query(text)
        self.assertEquals(parse_results['stripped_query'], 'some query text')
