import math
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from askbot.utils import functions
from askbot.utils.slug import slugify
from askbot.skins.loaders import get_template
from askbot.conf import settings as askbot_settings

register = template.Library()

GRAVATAR_TEMPLATE = (
                     '<a style="text-decoration:none" '
                     'href="%(user_profile_url)s"><img class="gravatar" '
                     'width="%(size)s" height="%(size)s" '
                     'src="http://www.gravatar.com/avatar/%(gravatar_hash)s'
                     '?s=%(size)s&amp;d=%(gravatar_type)s&amp;r=PG" '
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
    user_id = functions.get_from_dict_or_object(user, 'id')
    slug = slugify(user.username)
    user_profile_url = reverse(
                        'user_profile',
                        kwargs={'id':user_id, 'slug':slug}
                    )
    #safe_username = template.defaultfilters.urlencode(username)
    return mark_safe(GRAVATAR_TEMPLATE % {
        'user_profile_url': user_profile_url,
        'size': size,
        'gravatar_hash': functions.get_from_dict_or_object(user, 'gravatar'),
        'gravatar_type': askbot_settings.GRAVATAR_TYPE,
        'alt_text': _('%(username)s gravatar image') % {'username': user.username},
        'username': functions.get_from_dict_or_object(user, 'username'),
    })
    
@register.simple_tag
def get_tag_font_size(tags):
    max_tag = 0
    for tag in tags:
        if tag.used_count > max_tag:
            max_tag = tag.used_count

    min_tag = max_tag
    for tag in tags:
        if tag.used_count < min_tag:
            min_tag = tag.used_count

    font_size = {}
    for tag in tags:
        font_size[tag.name] = tag_font_size(max_tag,min_tag,tag.used_count)
    
    return font_size

@register.simple_tag
def tag_font_size(max_size, min_size, current_size):
    """
    do a logarithmic mapping calcuation for a proper size for tagging cloud
    Algorithm from http://blogs.dekoh.com/dev/2007/10/29/choosing-a-good-
    font-size-variation-algorithm-for-your-tag-cloud/
    """
    MAX_FONTSIZE = 10
    MIN_FONTSIZE = 1

    #avoid invalid calculation
    if current_size == 0:
        current_size = 1    
    try:
        weight = (math.log10(current_size) - math.log10(min_size)) / (math.log10(max_size) - math.log10(min_size))
    except Exception:
        weight = 0
        
    return int(MIN_FONTSIZE + round((MAX_FONTSIZE - MIN_FONTSIZE) * weight))

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


class IncludeJinja(template.Node):
    """http://www.mellowmorning.com/2010/08/24/"""
    def __init__(self, filename, request_var):
        self.filename = filename
        self.request_var = template.Variable(request_var)
    def render(self, context):
        request = self.request_var.resolve(context)
        jinja_template = get_template(self.filename, request)
        return jinja_template.render(context)

@register.tag
def include_jinja(parser, token):
    bits = token.contents.split()

    #Check if a filename was given
    if len(bits) != 3:
        error_message = '%r tag requires the name of the ' + \
                        'template and the request variable'
        raise template.TemplateSyntaxError(error_message % bits[0])
    filename = bits[1]
    request_var = bits[2]

    #Remove quotes or raise error
    if filename[0] in ('"', "'") and filename[-1] == filename[0]:
        filename = filename[1:-1]
    else:
        raise template.TemplateSyntaxError('file name must be quoted')

    return IncludeJinja(filename, request_var)
