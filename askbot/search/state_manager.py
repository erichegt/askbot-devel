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

    def is_default(self):
        """True if search state is default
        False otherwise, but with a few exceptions
        notably page_size has no effect here
        """
        if self.scope != const.DEFAULT_POST_SCOPE:
            return False
        if self.author:
            return False
        if self.query:
            return False
        if self.tags:
            return False
        return True

    def set_logged_out(self):
        if self.scope == 'favorite':
            self.scope = None
        self.logged_in = False

    def set_logged_in(self):
        self.logged_in = True

    def reset(self):
        #re-initialize, but keep login state
        is_logged_in = self.logged_in
        self.__init__()
        self.logged_in = is_logged_in

    def update_value(self, key, store):
        if key in store:
            old_value = getattr(self, key)
            new_value = store[key]
            if new_value != old_value:
                setattr(self, key, new_value)
                self.reset_page()

    def relax_stickiness(self, input_dict, view_log):
        if view_log.get_previous(1) == 'questions':
            if not some_in(ACTIVE_COMMANDS, input_dict):
                self.reset()
        #todo also relax if 'all' scope was clicked twice

    def update_from_user_input(self, input_dict):
        #todo: this function will probably not 
        #fit the case of multiple parameters entered at the same tiem
        if 'start_over' in input_dict:
            self.reset()

        if 'page' in input_dict:
            self.page = input_dict['page']
            #special case - on page flip no other input is accepted
            return

        if 'page_size' in input_dict:
            self.update_value('page_size', input_dict)
            self.reset_page()#todo may be smarter here - start with ~same q
            #same as with page - return right away
            return

        if 'scope' in input_dict:
            if input_dict['scope'] == 'favorite' and self.logged_in == False:
                self.reset_scope()
            else:
                self.update_value('scope', input_dict)

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

        self.update_value('author', input_dict)

        if 'query' in input_dict:
            query_bits = parse_query(input_dict['query'])
            tmp_input_dict = copy.deepcopy(input_dict)
            tmp_input_dict.update(query_bits)
            self.update_value('query', tmp_input_dict)#the original query
            #pull out values of [title:xxx], [user:some one]
            #[tag: sometag], title:'xxx', title:"xxx", @user, @'some user',
            #and  #tag - (hash symbol to delineate the tag
            self.update_value('stripped_query', tmp_input_dict)
            self.update_value('query_tags', tmp_input_dict)
            self.update_value('query_users', tmp_input_dict)
            self.update_value('query_title', tmp_input_dict)
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
                self.update_value('sort', input_dict)

        #todo: plug - mysql has no relevance sort
        if not askbot.conf.should_show_sort_by_relevance():
            if self.sort == 'relevance-desc':
                self.reset_sort()

    def update(self, input_dict, view_log, user):
        """update the search state according to the
        user input and the queue of the page hits that
        user made"""
        if 'preserve_state' in input_dict:
            return

        if view_log.should_reset_search_state():
            self.reset()

        if user.is_authenticated():
            self.set_logged_in()

        self.update_from_user_input(input_dict)
        self.relax_stickiness(input_dict, view_log)

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

    def reset_scope(self):
        self.scope = const.DEFAULT_POST_SCOPE

class ViewLog(object):
    """The ViewLog helper obejcts store the trail of the page visits for a
    given user. The trail is recorded only up to a certain depth.

    The purpose to record this info is to reset the search state
    when the user walks "too far away" from the search page.
    
    These objects must be modified only in this middlware.
    """
    def __init__(self):
        self.views = []
        self.depth = 3 #todo maybe move this to const.py

    def get_previous(self, num):
        """get a previous record from a certain depth"""
        if num > self.depth - 1:
            raise Exception("view log depth exceeded")
        elif num < 0:
            raise Exception("num must be positive")
        elif num <= len(self.views) - 1:
            return self.views[num]
        else:
            return None

    def should_reset_search_state(self):
        """return True if user stepped too far from the home page
        and False otherwise"""
        if self.get_previous(1) != 'questions':
            if self.get_previous(2) != 'questions':
                return True
        return False

    def set_current(self, view_name):
        """insert a new record"""
        self.views.insert(0, view_name)
        if len(self.views) > self.depth:
            self.views.pop()

    def __str__(self):
        return str(self.views) + ' depth=%d' % self.depth
