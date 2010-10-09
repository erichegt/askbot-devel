import time
import os
import datetime
import math
import re
import logging
from django import template
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from askbot.const import *
from askbot.models import Question, Answer, QuestionRevision, AnswerRevision
from askbot.models import Badge
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.conf import settings
from askbot.conf import settings as askbot_settings
from django.template.defaulttags import url as default_url
from django.core.urlresolvers import reverse
from askbot.skins import utils as skin_utils
from askbot.utils import colors
from askbot.utils import functions
from askbot.utils.slug import slugify
from askbot.templatetags import extra_filters
from askbot.skins.loaders import ENV

register = template.Library()

GRAVATAR_TEMPLATE = (
                     '<a style="text-decoration:none" '
                     'href="%(user_profile_url)s"><img class="gravatar" '
                     'width="%(size)s" height="%(size)s" '
                     'src="http://www.gravatar.com/avatar/%(gravatar_hash)s'
                     '?s=%(size)s&amp;d=identicon&amp;r=PG" '
                     'title="%(username)s" '
                     'alt="%(alt_text)s" /></a>')

@register.simple_tag
def gravatar(user, size):
    """
    Creates an ``<img>`` for a user's Gravatar with a given size.

    This tag can accept a User object, or a dict containing the
    appropriate values.
    """
    #todo: rewrite using get_from_dict_or_object
    gravatar = functions.get_from_dict_or_object(user, 'gravatar')
    username = functions.get_from_dict_or_object(user, 'username')
    user_id = functions.get_from_dict_or_object(user, 'id')
    slug = slugify(username)
    user_profile_url = reverse('user_profile', kwargs={'id':user_id,'slug':slug})
    #safe_username = template.defaultfilters.urlencode(username)
    return mark_safe(GRAVATAR_TEMPLATE % {
        'user_profile_url': user_profile_url,
        'size': size,
        'gravatar_hash': gravatar,
        'alt_text': _('%(username)s gravatar image') % {'username': username},
        'username': username,
    })

MAX_FONTSIZE = 18
MIN_FONTSIZE = 12
@register.simple_tag
def tag_font_size(max_size, min_size, current_size):
    """
    do a logarithmic mapping calcuation for a proper size for tagging cloud
    Algorithm from http://blogs.dekoh.com/dev/2007/10/29/choosing-a-good-font-size-variation-algorithm-for-your-tag-cloud/
    """
    #avoid invalid calculation
    if current_size == 0:
        current_size = 1
    try:
        weight = (math.log10(current_size) - math.log10(min_size)) / (math.log10(max_size) - math.log10(min_size))
    except:
        weight = 0
    return MIN_FONTSIZE + round((MAX_FONTSIZE - MIN_FONTSIZE) * weight)


#todo: this function may need to be removed to simplify the paginator functionality
LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 5
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 4
NUM_PAGES_OUTSIDE_RANGE = 1
ADJACENT_PAGES = 2
@register.inclusion_tag("paginator.html")
def cnprog_paginator(context):
    """
    custom paginator tag
    Inspired from http://blog.localkinegrinds.com/2007/09/06/digg-style-pagination-in-django/
    """
    if (context["is_paginated"]):
        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)

        if (context["pages"] <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [n for n in range(1, context["pages"] + 1) if n > 0 and n <= context["pages"]]
        elif (context["page"] <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1) if n > 0 and n <= context["pages"]]
            pages_outside_leading_range = [n + context["pages"] for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (context["page"] > context["pages"] - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [n for n in range(context["pages"] - TRAILING_PAGE_RANGE_DISPLAYED + 1, context["pages"] + 1) if n > 0 and n <= context["pages"]]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_numbers = [n for n in range(context["page"] - ADJACENT_PAGES, context["page"] + ADJACENT_PAGES + 1) if n > 0 and n <= context["pages"]]
            pages_outside_leading_range = [n + context["pages"] for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

        extend_url = context.get('extend_url', '')
        return {
            "base_url": context["base_url"],
            "is_paginated": context["is_paginated"],
            "previous": context["previous"],
            "has_previous": context["has_previous"],
            "next": context["next"],
            "has_next": context["has_next"],
            "page": context["page"],
            "pages": context["pages"],
            "page_numbers": page_numbers,
            "in_leading_range" : in_leading_range,
            "in_trailing_range" : in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range,
            "extend_url" : extend_url
        }

@register.inclusion_tag("post_contributor_info.html")
def post_contributor_info(post,contributor_type='original_author'):
    """contributor_type: original_author|last_updater
    """
    if isinstance(post,Question):
        post_type = 'question'
    elif isinstance(post,Answer):
        post_type = 'answer'
    elif isinstance(post,AnswerRevision) or isinstance(post,QuestionRevision):
        post_type = 'revision'
    return {
        'post':post,
        'post_type':post_type,
        'wiki_on':askbot_settings.WIKI_ON,
        'contributor_type':contributor_type
    }


BADGE_TEMPLATE = '<span title="%(pluralized_badge_count)s">' \
                + '<span class="%(badge_css_class)s">%(badge_symbol)s</span>' \
                + '<span class="badgecount">%(badge_count)s</span>' \
                + '</span>'
BADGE_LEVELS = dict(Badge.TYPE_CHOICES)

def render_badge_counter(badge_level = None, badge_count = None):

    pluralized_badge_count = ungettext(
                    '%(badge_count)d %(badge_level)s badge',
                    '%(badge_count)d %(badge_level)s badges',
                    badge_count
                ) % {
                        'badge_count': badge_count, 
                        'badge_level': BADGE_LEVELS[badge_level]
                    }

    output = BADGE_TEMPLATE % \
                        {
                            'pluralized_badge_count': pluralized_badge_count,
                            'badge_css_class': Badge.CSS_CLASSES[badge_level],
                            'badge_symbol': Badge.DISPLAY_SYMBOL,
                            'badge_count': badge_count,
                        }
    return output


REP_TEMPLATE = '<span class="reputation-score" ' \
                + 'title="%(reputation)s %(repword)s">%(reputation)s</span>'
@register.simple_tag
def render_reputation_counter(rep):
    return REP_TEMPLATE % {
        'repword': _('reputation points'),
        'reputation': rep
    }


@register.simple_tag
def render_badge_counters(gold_count, silver_count, bronze_count):
    output = ''
    if gold_count > 0 :
        output += render_badge_counter(
                                badge_level = Badge.GOLD,
                                badge_count = gold_count
                            )
    if silver_count > 0:
        output += render_badge_counter(
                                badge_level = Badge.SILVER,
                                badge_count = silver_count
                            )
    if bronze_count > 0:
        output += render_badge_counter(
                                badge_level = Badge.BRONZE,
                                badge_count = bronze_count
                            )
    return output


@register.simple_tag
def get_score_badge_by_details(rep, gold_count, silver_count, bronze_count):
    output = render_reputation_counter(rep)
    output += render_badge_counters(gold_count, silver_count, bronze_count)
    return output


#this one is used for the header next to user profile and logout links
REP_TEMPLATE2 = '<a class="ab-nav-karma" href="%(karma_graph_url)s" ' \
                + ' title="%(karma_phrase)s">' \
                + '%(rep_word)s: %(reputation)s</a>'
BADGE_TEMPLATE2 = '&nbsp;<a class="ab-nav-badges" href="%(user_badges_url)s">' \
                + '%(badge_counters)s</a>'
@register.simple_tag
def get_long_score_and_badge_report(user):
    profile_url = user.get_absolute_url()
    karma_graph_url = profile_url + '?sort=reputation'
    karma_phrase = _('your karma is %(reputation)s') \
                        % { 'reputation': user.reputation }

    output = REP_TEMPLATE2 % {
        'repword': _('reputation points'),
        'karma_graph_url': karma_graph_url,
        'reputation': user.reputation,
        'karma_phrase': karma_phrase,
        'rep_word': _('reputation points'),
    }

    badge_counters = render_badge_counters(user.gold, user.silver, user.bronze)

    if badge_counters != '':
        output += ' ' + BADGE_TEMPLATE2 % {
                        'user_badges_url': profile_url + '#badges',
                        'badge_counters': _('badges: ') + badge_counters
                    }
    return output


@register.simple_tag
def get_score_badge(user):
    return get_score_badge_by_details(
                        user.reputation,
                        user.gold,
                        user.silver,
                        user.bronze
                    )


@register.simple_tag
def get_user_vote_image(dic, key, arrow):
    if dic.has_key(key):
        if int(dic[key]) == int(arrow):
            return '-on'
    return ''
        
@register.simple_tag
def get_total_count(up_count, down_count):
    return up_count + down_count

@register.simple_tag
def format_number(value):
    strValue = str(value)
    if len(strValue) <= 3:
        return strValue
    result = ''
    first = ''
    pattern = re.compile('(-?\d+)(\d{3})')
    m = re.match(pattern, strValue)
    while m != None:
        first = m.group(1)
        second = m.group(2)
        result = ',' + second + result
        strValue = first + ',' + second
        m = re.match(pattern, strValue)
    return first + result

diff_date = register.simple_tag(functions.diff_date)

@register.simple_tag
def get_latest_changed_timestamp():
    try:
        from time import localtime, strftime
        from os import path
        root = settings.SITE_SRC_ROOT
        dir = (
            root,
            '%s/askbot' % root,
            '%s/templates' % root,
        )
        stamp = (path.getmtime(d) for d in dir)
        latest = max(stamp)
        timestr = strftime("%H:%M %b-%d-%Y %Z", localtime(latest))
    except:
        timestr = ''
    return timestr

@register.simple_tag
def media(url):
    url = skin_utils.get_media_url(url)
    if url:
        return url
    else:
        return '' #todo: raise exception here?

class ItemSeparatorNode(template.Node):
    def __init__(self,separator):
        sep = separator.strip()
        if sep[0] == sep[-1] and sep[0] in ('\'','"'):
            sep = sep[1:-1]
        else:
            raise template.TemplateSyntaxError('separator in joinitems tag must be quoted')
        self.content = sep
    def render(self,context):
        return self.content

class JoinItemListNode(template.Node):
    def __init__(self,separator=ItemSeparatorNode("''"), last_separator=None, items=()):
        self.separator = separator
        if last_separator:
            self.last_separator = last_separator
        else:
            self.last_separator = separator
        self.items = items
    def render(self,context):
        out = []
        empty_re = re.compile(r'^\s*$')
        for item in self.items:
            bit = item.render(context)
            if not empty_re.search(bit):
                out.append(bit)
        if len(out) == 1:
            return out[0]
        if len(out) > 1:
            last = out.pop()
            all_but_last = self.separator.render(context).join(out)
            return self.last_separator.render(context).join((all_but_last,last))
        else:
            assert(len(out)==0)
            return ''

@register.tag(name="joinitems")
def joinitems(parser,token):
    try:
        tagname, junk, sep_token = token.split_contents()
        last_sep_token = None
    except:
        try:
            tagname, junk, sep_token, last_sep_token = token.split_contents()
        except:
            raise template.TemplateSyntaxError('incorrect usage of joinitems tag first param '
                                            'must be \'using\' second - separator and '
                                            'optional third - last item separator')
    if junk == 'using':
        sep_node = ItemSeparatorNode(sep_token)
        if last_sep_token:
            last_sep_node = ItemSeparatorNode(last_sep_token)
        else:
            last_sep_node = None
    else:
        raise template.TemplateSyntaxError("joinitems tag requires 'using \"separator html\"' parameters")
    nodelist = []
    while True:
        nodelist.append(parser.parse(('separator','endjoinitems')))
        next = parser.next_token()
        if next.contents == 'endjoinitems':
            break

    return JoinItemListNode(separator=sep_node,last_separator=last_sep_node,items=nodelist)

class IncludeJinja(template.Node):
    """http://www.mellowmorning.com/2010/08/24/"""
    def __init__(self, filename):
        self.filename = filename
    def render(self, context):
        jinja_template = ENV.get_template(self.filename)
        return jinja_template.render(context)

@register.tag
def include_jinja(parser, token):
    bits = token.contents.split()

    #Check if a filename was given
    if len(bits) != 2:
        error_message = '%r tag requires the name of the ' + \
                        'template to be included included'
        raise template.TemplateSyntaxError(error_message % bits[0])
    filename = bits[1]

    #Remove quotes or raise error
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    else:
        raise template.TemplateSyntaxError('file name must be quoted')

    return IncludeJinja(filename)

class BlockMediaUrlNode(template.Node):
    def __init__(self,nodelist):
        self.items = nodelist 
    def render(self,context):
        url = ''
        if self.items:
            url += '/'     
        for item in self.items:
            url += item.render(context)

        url = skin_utils.get_media_url(url)
        return url.replace(' ','')

@register.tag(name='blockmedia')
def blockmedia(parser,token):
    try:
        tagname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("blockmedia tag does not use arguments")
    nodelist = []
    while True:
        nodelist.append(parser.parse(('endblockmedia')))
        next = parser.next_token()
        if next.contents == 'endblockmedia':
            break
    return BlockMediaUrlNode(nodelist)

class FullUrlNode(template.Node):
    def __init__(self, default_node):
        self.default_node = default_node

    def render(self, context):
        domain = askbot_settings.APP_URL
        #protocol = getattr(settings, "PROTOCOL", "http")
        path = self.default_node.render(context)
        return "%s%s" % (domain, path)

@register.tag(name='fullurl')
def fullurl(parser, token):
    default_node = default_url(parser, token)
    return FullUrlNode(default_node)

@register.simple_tag
def fullmedia(url):
    domain = askbot_settings.APP_URL
    #protocol = getattr(settings, "PROTOCOL", "http")
    path = media(url)
    return "%s%s" % (domain, path)

class IsManyNode(template.Node):
    def __init__(self, test_items, true_nodelist, false_nodelist):
        self.true_nodelist = true_nodelist
        self.false_nodelist = false_nodelist
        self.test_items = test_items 
    def render(self, context):
        maybe = False
        for item in self.test_items:
            is_good = item.resolve(context)
            if maybe == True and is_good:
                return self.true_nodelist.render(context)
            if is_good:
                maybe = True
        return self.false_nodelist.render(context)

@register.tag(name='ifmany')
def ifmany(parser,token):
    """usage {% ifmany item1 item2 item3 ... itemN %} stuff {% endifmany %}
    returns content included into the tag if more than one
    item evaluates to Tru'ish value - that's the idea
    {% else %} is not supported yet
    """

    bits = list(token.split_contents())
    start_tag = bits.pop(0)

    test_items = []
    for bit in bits:
        item = parser.compile_filter(bit)
        test_items.append(item)

    end_tag = 'end' + start_tag
    else_tag = 'else'
    true_nodelist = parser.parse((end_tag,else_tag,))
    token = parser.next_token()
    if token.contents == else_tag:
        false_nodelist = parser.parse((end_tag,))
        token = parser.next_token()
    else:
        false_nodelist = template.NodeList()

    return IsManyNode(test_items, true_nodelist, false_nodelist)
