"""Search state manager object"""
import re

from django.utils.http import urlquote

import askbot
import askbot.conf
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils.functions import strip_plus


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
    def __init__(self, scope, sort, query, tags, author, page, page_size, user_logged_in):
        # INFO: zip(*[('a', 1), ('b', 2)])[0] == ('a', 'b')

        if (scope not in zip(*const.POST_SCOPE_LIST)[0]) or (scope == 'favorite' and not user_logged_in):
            self.scope = const.DEFAULT_POST_SCOPE
        else:
            self.scope = scope

        if query:
            self.query = ' '.join(query.split('+')).strip()
            if self.query == '':
                self.query = None
        else:
            self.query = None

        if self.query:
            #pull out values of [title:xxx], [user:some one]
            #[tag: sometag], title:'xxx', title:"xxx", @user, @'some user',
            #and  #tag - (hash symbol to delineate the tag
            query_bits = parse_query(self.query)
            self.stripped_query = query_bits['stripped_query']
            self.query_tags = query_bits['query_tags']
            self.query_users = query_bits['query_users']
            self.query_title = query_bits['query_title']
        else:
            self.stripped_query = None
            self.query_tags = None
            self.query_users = None
            self.query_title = None

        if (sort not in zip(*const.POST_SORT_METHODS)[0]) or (sort == 'relevance-desc' and (not self.query or not askbot.conf.should_show_sort_by_relevance())):
            self.sort = const.DEFAULT_POST_SORT_METHOD
        else:
            self.sort = sort

        if tags:
            # const.TAG_SPLIT_REGEX, const.TAG_REGEX
            #' '.join(tags.split('+'))
            self.tags = tags.split('+')
        else:
            self.tags = None

        if author:
            self.author = int(author)
        else:
            self.author = None

        if page:
            self.page = int(page)
        else:
            self.page = 1

        if not page_size or page_size not in zip(*const.PAGE_SIZE_CHOICES)[0]:
            self.page_size = int(askbot_settings.DEFAULT_QUESTIONS_PAGE_SIZE)
        else:
            self.page_size = int(page_size)

    def __str__(self):
        out = 'scope=%s\n' % self.scope
        out += 'query=%s\n' % self.query
        if self.tags:
            out += 'tags=%s\n' % ','.join(self.tags)
        out += 'author=%s\n' % self.author
        out += 'sort=%s\n' % self.sort
        out += 'page_size=%d\n' % self.page_size
        out += 'page=%d\n' % self.page
        return out

    def query_string(self):
        out = 'scope:%s' % self.scope
        out += '/sort:%s' % self.sort
        if self.query:
            out += '/query:%s' % urlquote(self.query)
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
