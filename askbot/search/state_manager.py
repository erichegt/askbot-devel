#search state manager object
#that lives in the session and takes care of the state
#persistece during the search session
import askbot
import askbot.conf
from askbot import const
from askbot.conf import settings as askbot_settings
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

class SearchState(object):
    def __init__(self):
        self.scope = const.DEFAULT_POST_SCOPE
        self.query = None
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
            self.update_value('query', input_dict)
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
        return False
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
