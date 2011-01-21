from django.test import TestCase
from askbot.search.state_manager import SearchState, ViewLog

class SearchStateTests(TestCase):
    def setUp(self):
        self.state = SearchState()
        self.log = ViewLog()

    def visit_page(self, page_name):
        """page_name is name of the view function
        that is to be "visited"
        """
        self.log.set_current(page_name)

    def update(self, data):
        self.visit_page('questions')
        self.state.update(data, self.log)

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
        self.update({'reset_query':True})
        self.assertEquals(self.state.query, None)
        self.assert_tags_are('tag1')
