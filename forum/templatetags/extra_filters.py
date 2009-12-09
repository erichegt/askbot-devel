from django import template
from django.core import serializers
from forum import auth
import logging

register = template.Library()

@template.defaultfilters.stringfilter
@register.filter
def collapse(input):
    return ' '.join(input.split())

@register.filter
def can_moderate_users(user):
    return auth.can_moderate_users(user)

@register.filter
def can_vote_up(user):
    return auth.can_vote_up(user)

@register.filter
def can_flag_offensive(user):
    return auth.can_flag_offensive(user)

@register.filter
def can_add_comments(user,subject):
    return auth.can_add_comments(user,subject)

@register.filter
def can_vote_down(user):
    return auth.can_vote_down(user)

@register.filter
def can_retag_questions(user):
    return auth.can_retag_questions(user)

@register.filter
def can_edit_post(user, post):
    return auth.can_edit_post(user, post)

@register.filter
def can_delete_comment(user, comment):
    return auth.can_delete_comment(user, comment)

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
    return auth.can_delete_post(user, post)
    
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
            return "<span class=""thousand"">%sk</span>" % string
        else:
            return number
    except:
        return number

@register.filter
def json_serialize(object):
    return serializers.serialize('json',object)
