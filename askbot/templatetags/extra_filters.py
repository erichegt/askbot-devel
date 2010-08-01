from django import template
from django.core import exceptions
from askbot import auth
from askbot import models
from askbot.deps.grapefruit import Color
from django.utils.translation import ugettext as _
import logging

register = template.Library()

@template.defaultfilters.stringfilter
@register.filter
def collapse(input):
    return ' '.join(input.split())

@register.filter
def can_moderate_user(user, other_user):
    if user.is_authenticated() and user.can_moderate_user(other_user):
        return True
    return False

@register.filter
def can_flag_offensive(user):
    return auth.can_flag_offensive(user)

@register.filter
def can_add_comments(user, subject):
    return auth.can_add_comments(user, subject)

@register.filter
def can_retag_questions(user):
    return auth.can_retag_questions(user)

@register.filter
def can_edit_post(user, post):
    return auth.can_edit_post(user, post)

@register.filter
def can_delete_comment(user, comment):
    if user.is_anonymous():
        return False
    try:
        user.assert_can_delete_comment(comment)
        return True
    except exceptions.PermissionDenied:
        return False

@register.filter
def can_view_offensive_flags(user):
    return auth.can_view_offensive_flags(user)

@register.filter
def can_close_question(user, question):
    return auth.can_close_question(user, question)

@register.filter
def can_lock_posts(user):
    return auth.can_lock_posts(user)
    
@register.filter
def can_accept_answer(user, question, answer):
    return auth.can_accept_answer(user, question, answer)
    
@register.filter
def can_reopen_question(user, question):
    return auth.can_reopen_question(user, question)

@register.filter
def can_delete_post(user, post):
    if user.is_anonymous():
        return False
    try:
        if isinstance(post, models.Question):
            user.assert_can_delete_question(question = post)
            return True
        elif isinstance(post, models.Answer):
            user.assert_can_delete_answer(answer = post)
            return True
        else:
            return False
    except exceptions.PermissionDenied:
        return False
    
@register.filter
def can_view_user_edit(request_user, target_user):
    return auth.can_view_user_edit(request_user, target_user)
    
@register.filter
def can_view_user_votes(request_user, target_user):
    return auth.can_view_user_votes(request_user, target_user)
    
@register.filter
def can_view_user_preferences(request_user, target_user):
    return auth.can_view_user_preferences(request_user, target_user)
    
@register.filter
def is_user_self(request_user, target_user):
    return auth.is_user_self(request_user, target_user)
    
@register.filter
def cnprog_intword(number):
    try:
        if 1000 <= number < 10000:
            string = str(number)[0:1]
            return '<span class="thousand">%sk</span>' % string
        else:
            return number
    except:
        return number

@register.filter
def humanize_counter(number):
    if number == 0:
        return _('no items in counter')
    elif number >= 1000:
        number = number/1000
        s = '%.1f' % number
        if s.endswith('.0'):
            return s[:-2] + 'k'
        else:
            return s + 'k'
    else:
        return str(number)

@register.filter
def absolute_value(number):
    return abs(number)
