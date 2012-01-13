from askbot.tests.utils import AskbotTestCase
from askbot.search.state_manager import SearchState
import askbot.conf


class SearchStateTests(AskbotTestCase):
    def _ss(self, query=None, tags=None):
        return SearchState(
            scope=None,
            sort=None,
            query=query,
            tags=tags,
            author=None,
            page=None,
            page_size=None,

            user_logged_in=False
        )

    def test_no_selectors(self):
        ss = self._ss()
        self.assertEqual(
            'scope:all/sort:activity-desc/page_size:30/page:1/',  # search defaults
            ss.query_string()
        )

    def test_buggy_selectors(self):
        ss = SearchState(
            scope='blah1',
            sort='blah2',
            query=None,
            tags=None,

            # INFO: URLs for the following selectors accept only digits!
            author=None,
            page='0',
            page_size='59',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:all/sort:activity-desc/page_size:30/page:1/',  # search defaults
            ss.query_string()
        )

    def test_all_valid_selectors(self):
        ss = SearchState(
            scope='unanswered',
            sort='age-desc',
            query=' alfa',
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:unanswered/sort:age-desc/query:alfa/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()
        )

    def test_edge_cases_1(self):
        ss = SearchState(
            scope='favorite', # this is not a valid choice for non-logger users
            sort='age-desc',
            query=' alfa',
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:all/sort:age-desc/query:alfa/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()
        )

        ss = SearchState(
            scope='favorite',
            sort='age-desc',
            query=' alfa',
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=True
        )
        self.assertEqual(
            'scope:favorite/sort:age-desc/query:alfa/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()

        )

    def test_edge_cases_2(self):
        old_func = askbot.conf.should_show_sort_by_relevance
        askbot.conf.should_show_sort_by_relevance = lambda: True # monkey patch

        ss = SearchState(
            scope='all',
            sort='relevance-desc',
            query='hejho',
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:all/sort:relevance-desc/query:hejho/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()
        )

        ss = SearchState(
            scope='all',
            sort='relevance-desc', # this is not a valid choice for empty queries
            query=None,
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:all/sort:activity-desc/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()
        )

        askbot.conf.should_show_sort_by_relevance = lambda: False # monkey patch

        ss = SearchState(
            scope='all',
            sort='relevance-desc', # this is also invalid for db-s other than Postgresql
            query='hejho',
            tags='miki, mini',
            author='12',
            page='2',
            page_size='50',

            user_logged_in=False
        )
        self.assertEqual(
            'scope:all/sort:activity-desc/query:hejho/tags:miki,mini/author:12/page_size:50/page:2/',
            ss.query_string()
        )

        askbot.conf.should_show_sort_by_relevance = old_func

    def test_query_escaping(self):
        ss = self._ss(query=' alfa miki maki +-%#?= lalala/: ') # query coming from URL is already unescaped
        self.assertEqual(
            'scope:all/sort:activity-desc/query:alfa%20miki%20maki%20+-%25%23%3F%3D%20lalala%2F%3A/page_size:30/page:1/',
            ss.query_string()
        )

    def test_tag_escaping(self):
        ss = self._ss(tags=' aA09_+.-#, miki ') # tag string coming from URL is already unescaped
        self.assertEqual(
            'scope:all/sort:activity-desc/tags:aA09_+.-%23,miki/page_size:30/page:1/',
            ss.query_string()
        )

    def test_extract_users(self):
        ss = self._ss(query='"@anna haha @"maria fernanda" @\'diego maradona\' hehe [user:karl  marx] hoho  user:\' george bush  \'')
        self.assertEquals(
            sorted(ss.query_users),
            sorted(['anna', 'maria fernanda', 'diego maradona', 'karl marx', 'george bush'])
        )
        self.assertEquals(ss.stripped_query, '" haha hehe hoho')
        self.assertEqual(
            'scope:all/sort:activity-desc/query:%22%40anna%20haha%20%40%22maria%20fernanda%22%20%40%27diego%20maradona%27%20hehe%20%5Buser%3Akarl%20%20marx%5D%20hoho%20%20user%3A%27%20george%20bush%20%20%27/page_size:30/page:1/',
            ss.query_string()
        )

    def test_extract_tags(self):
        ss = self._ss(query='#tag1 [tag: tag2] some text [tag3] query')
        self.assertEquals(set(ss.query_tags), set(['tag1', 'tag2', 'tag3']))
        self.assertEquals(ss.stripped_query, 'some text query')

    def test_extract_title1(self):
        ss = self._ss(query='some text query [title: what is this?]')
        self.assertEquals(ss.query_title, 'what is this?')
        self.assertEquals(ss.stripped_query, 'some text query')

    def test_extract_title2(self):
        ss = self._ss(query='some text query title:"what is this?"')
        self.assertEquals(ss.query_title, 'what is this?')
        self.assertEquals(ss.stripped_query, 'some text query')

    def test_extract_title3(self):
        ss = self._ss(query='some text query title:\'what is this?\'')
        self.assertEquals(ss.query_title, 'what is this?')
        self.assertEquals(ss.stripped_query, 'some text query')

    def test_negative_match(self):
        ss = self._ss(query='some query text')
        self.assertEquals(ss.stripped_query, 'some query text')
