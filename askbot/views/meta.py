"""
:synopsis: remaining "secondary" views for askbot

This module contains a collection of views displaying all sorts of secondary and mostly static content.
"""
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views import static
from askbot.forms import FeedbackForm
from askbot.utils.forms import get_next_url
from askbot.models import Badge, Award
from askbot.skins.loaders import ENV
from askbot import skins
import askbot

def generic_view(request, template = None):
    print 'in generic view'
    template = ENV.get_template(template)
    context = RequestContext(request)
    return HttpResponse(template.render(context))

def about(request, template='about.html'):
    return generic_view(request, template) 

def page_not_found(request, template='404.html'):
    return generic_view(request, template) 

def server_error(request, template='500.html'):
    return generic_view(request, template) 

def faq(request):
    template = ENV.get_template('faq.html')
    data = {
        'view_name':'faq',
        'gravatar_faq_url': reverse('faq') + '#gravatar',
        #'send_email_key_url': reverse('send_email_key'),
        'ask_question_url': reverse('ask'),
    }
    context = RequestContext(request, data)
    return HttpResponse(template.render(context))

def feedback(request):
    data = {'view_name':'feedback'}
    form = None
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                data['email'] = form.cleaned_data.get('email',None)
            data['message'] = form.cleaned_data['message']
            data['name'] = form.cleaned_data.get('name',None)
            message = render_to_response('feedback_email.txt',data,context_instance=RequestContext(request))
            askbot.mail_moderators(_('Q&A forum feedback'), message)
            msg = _('Thanks for the feedback!')
            request.user.message_set.create(message=msg)
            return HttpResponseRedirect(get_next_url(request))
    else:
        form = FeedbackForm(initial={'next':get_next_url(request)})

    data['form'] = form
    context = RequestContext(request, data)
    template = ENV.get_template('feedback.html')
    return HttpResponse(template.render(context))
feedback.CANCEL_MESSAGE=_('We look forward to hearing your feedback! Please, give it next time :)')

def privacy(request):
    context = RequestContext(request, {'view_name':'privacy'})
    template = ENV.get_template('privacy.html')
    return HttpResponse(template.render(context)) 

def logout(request):#refactor/change behavior?
#currently you click logout and you get
#to this view which actually asks you again - do you really want to log out?
#I guess rationale was to tell the user that s/he may be still logged in
#through their external login sytem and we'd want to remind them about it
#however it might be a little annoying
#why not just show a message: you are logged out of forum, but
#if you really want to log out -> go to your openid provider
    data = {
        'view_name':'logout',
        'next' : get_next_url(request),
    }
    context = RequestContext(request, data)
    template = ENV.get_template('logout.html')
    return HttpResponse(template.render(context))

def badges(request):#user status/reputation system
    badges = Badge.objects.all().order_by('name')
    my_badges = []
    if request.user.is_authenticated():
        my_badges = Award.objects.filter(user=request.user).values('badge_id')
        #my_badges.query.group_by = ['badge_id']

    template = ENV.get_template('badges.html')
    data = {
        'active_tab': 'badges',
        'badges' : badges,
        'view_name': 'badges',
        'mybadges' : my_badges,
        'feedback_faq_url' : reverse('feedback'),
    }
    context = RequestContext(request, data)
    return HttpResponse(template.render(context))

def badge(request, id):
    badge = get_object_or_404(Badge, id=id)
    awards = Award.objects.extra(
        select={'id': 'auth_user.id', 
                'name': 'auth_user.username', 
                'rep':'auth_user.reputation', 
                'gold': 'auth_user.gold', 
                'silver': 'auth_user.silver', 
                'bronze': 'auth_user.bronze'},
        tables=['award', 'auth_user'],
        where=['badge_id=%s AND user_id=auth_user.id'],
        params=[id]
    ).distinct('id')

    template = ENV.get_template('badge.html')
    data = {
        'view_name': badge,
        'active_tab': 'badges',
        'awards' : awards,
        'badge' : badge,
    }
    context = RequestContext(request, data)
    return HttpResponse(template.render(context))

def media(request, skin, resource):
    """view that serves static media from any skin
    uses django static serve view, where document root is
    adjusted according to the current skin selection

    in production this views should be by-passed via server configuration
    for the better efficiency of serving static files
    """
    dir = skins.utils.get_path_to_skin(skin)
    return static.serve(request, '/media/' + resource, document_root = dir)
