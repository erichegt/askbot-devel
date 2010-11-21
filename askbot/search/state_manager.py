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
    'reset_query', 'reset_author', 'reset_tags',
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

    def update_from_user_input(self, input_dict, unprocessed_input = {}):
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
            return

        self.update_value('author', input_dict)

        if 'query' in input_dict:
            self.update_value('query', input_dict)
            self.sort = 'relevance-desc'
        elif 'search' in unprocessed_input:#a case of use nulling search query by hand
            self.reset_query()
            return

        if 'sort' in input_dict:
            if input_dict['sort'] == 'relevance-desc' and self.query is None:
                self.reset_sort()
            else:
                self.update_value('sort', input_dict)

        #todo: plug - mysql has no relevance sort
        if not askbot.conf.should_show_sort_by_relevance():
            if self.sort == 'relevance-desc':
                self.reset_sort()

    def reset_page(self):
        self.page = 1

    def reset_query(self):
        if self.query:
            self.query = None
            self.reset_page()
            if self.sort == 'relevance-desc':
                self.reset_sort()

    def reset_sort(self):
        self.sort = const.DEFAULT_POST_SORT_METHOD

    def reset_scope(self):
        self.scope = const.DEFAULT_POST_SCOPE
