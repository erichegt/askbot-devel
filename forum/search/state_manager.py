#search state manager object
#that lives in the session and takes care of the state
#persistece during the search session
from forum import const
import logging

class SearchState(object):
    def __init__(self):
        self.scope= const.DEFAULT_POST_SCOPE
        self.query = None
        self.tags = None
        self.author = None
        self.sort = const.DEFAULT_POST_SORT_METHOD
        self.page_size = const.DEFAULT_QUESTIONS_PAGE_SIZE
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

    def update_from_user_input(self,input, raw_input = {}):
        #todo: this function will probably not 
        #fit the case of multiple parameters entered at the same tiem
        if 'start_over' in input:
            self.reset()

        if 'page' in input:
            self.page = input['page']
            #special case - on page flip no other input is accepted
            return

        if 'page_size' in input:
            self.update_value('page_size',input)
            self.reset_page()#todo may be smarter here - start with ~same q
            #same as with page - return right away
            return

        if 'scope' in input:
            if input['scope'] == 'favorite' and self.logged_in == False:
                self.reset_scope()
            else:
                self.update_value('scope',input)

        if 'tags' in input:
            if self.tags:
                old_tags = self.tags.copy()
                self.tags = self.tags.union(input['tags'])
                if self.tags != old_tags:
                    self.reset_page()
            else:
                self.tags = input['tags']

        #all resets just return
        if 'reset_tags' in input:
            if self.tags:
                self.tags = None
                self.reset_page()
            return

        #todo: handle case of deleting tags one-by-one
        if 'reset_author' in input:
            if self.author:
                self.author = None
                self.reset_page()
            return

        if 'reset_query' in input:
            self.reset_query()
            return

        self.update_value('author',input)

        if 'query' in input:
            self.update_value('query',input)
            self.sort = 'relevant'
        elif 'search' in raw_input:#a case of use nulling search query by hand
            self.reset_query()
            return


        if 'sort' in input:
            if input['sort'] == 'relevant' and self.query is None:
                self.reset_sort()
            else:
                self.update_value('sort',input)

    def reset_page(self):
        self.page = 1

    def reset_query(self):
        if self.query:
            self.query = None
            self.reset_page()
            if self.sort == 'relevant':
                self.reset_sort()

    def reset_sort(self):
        self.sort = const.DEFAULT_POST_SORT_METHOD

    def reset_scope(self):
        self.scope = const.DEFAULT_POST_SCOPE
