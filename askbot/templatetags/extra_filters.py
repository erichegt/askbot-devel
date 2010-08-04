from django import template
from django.core import exceptions as django_exceptions
from askbot import exceptions as askbot_exceptions
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

def make_test_from_permission_assertion(
                                assertion_name = None,
                                allowed_exception = None
                            ):
    """a decorator-like function that will create a True/False test from
    permission assertion
    """
    def test_function(user, post):
        if user.is_anonymous():
            return False

        assertion = getattr(user, assertion_name)
        if allowed_exception:
            try:
                assertion(post)
                return True
            except allowed_exception:
                return True
            except django_exceptions.PermissionDenied:
                return False
        else:
            try:
                assertion(post)
                return True
            except django_exceptions.PermissionDenied:
                return False

    return test_function 


@register.filter
def can_moderate_user(user, other_user):
    if user.is_authenticated() and user.can_moderate_user(other_user):
        return True
    return False

can_flag_offensive = make_test_from_permission_assertion(
                        assertion_name = 'assert_can_flag_offensive',
                        allowed_exception = askbot_exceptions.DuplicateCommand
                    )
register.filter('can_flag_offensive', can_flag_offensive)

can_post_comment = make_test_from_permission_assertion(
                        assertion_name = 'assert_can_post_comment'
                    )
register.filter('can_post_comment', can_post_comment)

can_delete_comment = make_test_from_permission_assertion(
                        assertion_name = 'assert_can_delete_comment'
                    )
register.filter('can_delete_comment', can_delete_comment)

@register.filter
def can_retag_questions(user):
    return auth.can_retag_questions(user)

@register.filter
def can_edit_post(user, post):
    return auth.can_edit_post(user, post)

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
    except django_exceptions.PermissionDenied:
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
