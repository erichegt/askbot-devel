#search state manager object
#that lives in the session and takes care of the state
#persistece during the search session
import re
import copy
import askbot
import askbot.conf
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils.functions import strip_plus
import logging

ACTIVE_COMMANDS = (
    'sort', 'search', 'query',
    'reset_query', 'reset_author', 'reset_tags', 'remove_tag',
    'tags', 'scope', 'page_size', 'start_over',
    'page'
)

def some_in(what, where):
    for element in what:
        if element in where:
            return True
    return False

def extract_matching_token(text, regexes):
    """if text matches any of the regexes,
    * the entire match is removed from text
    * repeating spaces in the remaining string are replaced with one
    * returned is a tuple of: first group from the regex, remaining text
    """
    for regex in regexes:
        m = regex.search(text)
        if m:
            text = regex.sub('', text)
            extracted_match = m.group(1)
            return (strip_plus(extracted_match), strip_plus(text))
    return ('', text.strip())

def extract_all_matching_tokens(text, regexes):
    """the same as the ``extract_matching_token``
    but returns a tuple of: list of first group matches from the regexes
    and the remains of the input text
    """
    matching_tokens = set()
    for regex in regexes:
        matches = regex.findall(text)
        if len(matches) > 0:
            text = regex.sub('', text)
            matching_tokens.update([match.strip() for match in matches])
    return ([strip_plus(token) for token in matching_tokens], strip_plus(text))


def parse_query(query):
    """takes hand-typed search query string as an argument
    returns a dictionary with keys (and values in parens):
    * stripped_query (query with the items below stripped)
    * query_tags (list of tag names)
    * query_users (list of user names, not validated)
    * query_title (question title)
    Note: the stripped_query is the actual string
    against which global search will be performed
    the original query will still all be shown in the search
    query input box
    """
    title_re1 = re.compile(r'\[title:(.+?)\]')
    title_re2 = re.compile(r'title:"([^"]+?)"')
    title_re3 = re.compile(r"title:'([^']+?)'")
    title_regexes = (title_re1, title_re2, title_re3)
    (query_title, query) = extract_matching_token(query, title_regexes)

    tag_re1 = re.compile(r'\[([^:]+?)\]')
    tag_re2 = re.compile(r'\[tag:\s*([\S]+)\s*]')
    tag_re3 = re.compile(r'#(\S+)')
    tag_regexes = (tag_re1, tag_re2, tag_re3)
    (query_tags, query) = extract_all_matching_tokens(query, tag_regexes)

    user_re1 = re.compile(r'\[user:([^\]]+?)\]')
    user_re2 = re.compile(r'user:"([^"]+?)"')
    user_re3 = re.compile(r"user:'([^']+?)'")
    user_re4 = re.compile(r"""@([^'"\s]+)""")
    user_re5 = re.compile(r'@"([^"]+)"')
    user_re6 = re.compile(r"@'([^']+)'")
    user_regexes = (user_re1, user_re2, user_re3, user_re4, user_re5, user_re6)
    (query_users, stripped_query) = extract_all_matching_tokens(query, user_regexes)

    return {
        'stripped_query': stripped_query,
        'query_title': query_title,
        'query_tags': query_tags,
        'query_users': query_users
    }

class SearchState(object):
    def __init__(self):
        self.scope = const.DEFAULT_POST_SCOPE
        self.query = None
        self.stripped_query = None
        self.query_tags = []
        self.query_users = []
        self.query_title = None
        self.search = None
        self.tags = None
        self.author = None
        self.sort = const.DEFAULT_POST_SORT_METHOD
        self.page_size = int(askbot_settings.DEFAULT_QUESTIONS_PAGE_SIZE)
        self.page = 1
        self.logged_in = False
        logging.debug('new search state initialized')

    def __str__(self):
        out = 'scope=%s\n' % self.scope
        out += 'query=%s\n' % self.query
        if hasattr(self, 'search'):
            manual_search = (self.search == 'search')
            out += 'manual_search = %s\n' % str(manual_search)
        if self.tags:
            out += 'tags=%s\n' % ','.join(self.tags)
        out += 'author=%s\n' % self.author
        out += 'sort=%s\n' % self.sort
        out += 'page_size=%d\n' % self.page_size
        out += 'page=%d\n' % self.page
        out += 'logged_in=%s\n' % str(self.logged_in)
        return out

    def reset(self):
        #re-initialize, but keep login state
        is_logged_in = self.logged_in
        self.__init__()
        self.logged_in = is_logged_in

    def update_value(self, key, store, reset_page=True):
        if key in store:
            old_value = getattr(self, key)
            new_value = store[key]
            if new_value != old_value:
                setattr(self, key, new_value)
                if reset_page == True:
                    self.reset_page()

    def update_from_user_input(self, input_dict, user_logged_in):
        #todo: this function will probably not 
        #fit the case of multiple parameters entered at the same tiem
        if 'start_over' in input_dict:
            self.reset()

        reset_page = True
        if 'page' in input_dict:
            self.page = input_dict['page']
            reset_page = False # This is done to keep page from resetting in other sorting modes

        if 'page_size' in input_dict:
            self.update_value('page_size', input_dict)
            self.reset_page()#todo may be smarter here - start with ~same q

        if 'scope' in input_dict:
            if input_dict['scope'] == 'favorite' and not user_logged_in:
                self.scope = const.DEFAULT_POST_SCOPE
            else:
                self.update_value('scope', input_dict, reset_page=reset_page)

        if 'tags' in input_dict:
            if self.tags:
                old_tags = self.tags.copy()
                self.tags = self.tags.union(input_dict['tags'])
                if self.tags != old_tags:
                    self.reset_page()
            else:
                self.tags = input_dict['tags']

        if 'remove_tag' in input_dict and self.tags:
            rm_set = set([input_dict['remove_tag']])
            self.tags -= rm_set
            return

        #all resets just return
        if 'reset_tags' in input_dict:
            if self.tags:
                self.tags = None
                self.reset_page()
            return

        #todo: handle case of deleting tags one-by-one
        if 'reset_author' in input_dict:
            if self.author:
                self.author = None
                self.reset_page()
            return

        if 'reset_query' in input_dict:
            self.reset_query()
            if input_dict.get('sort', None) == 'relevance-desc':
                self.reset_sort()
            return

        self.update_value('author', input_dict, reset_page=reset_page)

        if 'query' in input_dict:
            query_bits = parse_query(input_dict['query'])
            tmp_input_dict = copy.deepcopy(input_dict)
            tmp_input_dict.update(query_bits)
            self.update_value('query', tmp_input_dict, reset_page=reset_page)#the original query
            #pull out values of [title:xxx], [user:some one]
            #[tag: sometag], title:'xxx', title:"xxx", @user, @'some user',
            #and  #tag - (hash symbol to delineate the tag
            self.update_value('stripped_query', tmp_input_dict, reset_page=reset_page)
            self.update_value('query_tags', tmp_input_dict, reset_page=reset_page)
            self.update_value('query_users', tmp_input_dict, reset_page=reset_page)
            self.update_value('query_title', tmp_input_dict, reset_page=reset_page)
            self.sort = 'relevance-desc'
        elif 'search' in input_dict:
            #a case of use nulling search query by hand
            #this branch corresponds to hitting search button manually
            #when the search query is empty
            self.reset_query()
            return
        elif askbot_settings.DECOUPLE_TEXT_QUERY_FROM_SEARCH_STATE:
            #no query in the request and the setting instructs to
            #not have the text search query sticky
            self.reset_query()

        if 'sort' in input_dict:
            if input_dict['sort'] == 'relevance-desc' and self.query is None:
                self.reset_sort()
            else:
                self.update_value('sort', input_dict, reset_page=reset_page)

        #todo: plug - mysql has no relevance sort
        if not askbot.conf.should_show_sort_by_relevance():
            if self.sort == 'relevance-desc':
                self.reset_sort()

    def reset_page(self):
        self.page = 1

    def reset_query(self):
        """reset the search query string and 
        the associated "sort by relevance command"
        """
        if self.query:
            self.query = None
            self.reset_page()
            if self.sort == 'relevance-desc':
                self.reset_sort()

    def reset_sort(self):
        self.sort = const.DEFAULT_POST_SORT_METHOD


    def query_string(self):
        out = 'section:%s' % self.scope
        out += '/sort:%s' % self.sort
        if self.query:
            out += '/query:%s' % '+'.join(self.query.split(' '))
        if self.tags:
            out += '/tags:%s' % '+'.join(self.tags)
        if self.author:
            out += '/author:%s' % self.author
        return out+'/'

    def make_parameters(self):
        params_dict = {
            'scope': self.scope,
            'sort': self.sort,
            'query': '+'.join(self.query.split(' ')) if self.query else None,
            'tags': '+'.join(self.tags) if self.tags else None,
            'author': self.author,
            'page_size': self.page_size
        }
        return params_dict
