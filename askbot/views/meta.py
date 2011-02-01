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
from django.db.models import Max, Count
from askbot.forms import FeedbackForm
from askbot.utils.forms import get_next_url
from askbot.utils.mail import mail_moderators
from askbot.models import BadgeData, Award, User
from askbot.models import badges as badge_data
from askbot.skins.loaders import render_into_skin
from askbot.conf import settings as askbot_settings
from askbot import skins

def generic_view(request, template = None, page_class = None):
    """this may be not necessary, since it is just a rewrite of render_into_skin"""
    return render_into_skin(template, {'page_class': page_class}, request)

def config_variable(request, variable_name = None, mimetype = None):
    """Print value from the configuration settings
    as response content. All parameters are required.
    """
    output = getattr(askbot_settings, variable_name, '')
    return HttpResponse(output, mimetype = mimetype)

def about(request, template='about.html'):
    return generic_view(request, template = template, page_class = 'meta') 

def page_not_found(request, template='404.html'):
    return generic_view(request, template) 

def server_error(request, template='500.html'):
    return generic_view(request, template) 

def faq(request):
    data = {
        'gravatar_faq_url': reverse('faq') + '#gravatar',
        #'send_email_key_url': reverse('send_email_key'),
        'ask_question_url': reverse('ask'),
        'page_class': 'meta',
    }
    return render_into_skin('faq.html', data, request)

def feedback(request):
    data = {'page_class': 'meta'}
    form = None
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            if not request.user.is_authenticated:
                data['email'] = form.cleaned_data.get('email',None)
            data['message'] = form.cleaned_data['message']
            data['name'] = form.cleaned_data.get('name',None)
            message = render_to_response('feedback_email.txt',data,context_instance=RequestContext(request))
            mail_moderators(_('Q&A forum feedback'), message)
            msg = _('Thanks for the feedback!')
            request.user.message_set.create(message=msg)
            return HttpResponseRedirect(get_next_url(request))
    else:
        form = FeedbackForm(initial={'next':get_next_url(request)})

    data['form'] = form
    return render_into_skin('feedback.html', data, request)
feedback.CANCEL_MESSAGE=_('We look forward to hearing your feedback! Please, give it next time :)')

def privacy(request):
    return render_into_skin('privacy.html', {'page_class': 'meta'}, request)

def logout(request):#refactor/change behavior?
#currently you click logout and you get
#to this view which actually asks you again - do you really want to log out?
#I guess rationale was to tell the user that s/he may be still logged in
#through their external login sytem and we'd want to remind them about it
#however it might be a little annoying
#why not just show a message: you are logged out of forum, but
#if you really want to log out -> go to your openid provider
    data = {
        'next' : get_next_url(request),
        'page_class': 'meta',
    }
    return render_into_skin('logout.html', data, request)

def badges(request):#user status/reputation system
    #todo: supplement database data with the stuff from badges.py
    known_badges = badge_data.BADGES.keys() 
    badges = BadgeData.objects.filter(slug__in = known_badges).order_by('slug')
    my_badges = []
    if request.user.is_authenticated():
        my_badges = Award.objects.filter(
                                user=request.user
                            ).values(
                                'badge_id'
                            ).distinct()
        #my_badges.query.group_by = ['badge_id']

    data = {
        'active_tab': 'badges',
        'badges' : badges,
        'page_class': 'meta',
        'mybadges' : my_badges,
        'feedback_faq_url' : reverse('feedback'),
    }
    return render_into_skin('badges.html', data, request)

def badge(request, id):
    #todo: supplement database data with the stuff from badges.py
    badge = get_object_or_404(BadgeData, id=id)
    badge_recipients = User.objects.filter(
                            award_user__badge = badge
                        ).annotate(
                            last_awarded_at = Max('award_user__awarded_at'),
                            award_count = Count('award_user')
                        ).order_by(
                            '-last_awarded_at'
                        )

    data = {
        'active_tab': 'badges',
        'badge_recipients' : badge_recipients,
        'badge' : badge,
        'page_class': 'meta',
    }
    return render_into_skin('badge.html', data, request)

def media(request, skin, resource):
    """view that serves static media from any skin
    uses django static serve view, where document root is
    adjusted according to the current skin selection

    in production this views should be by-passed via server configuration
    for the better efficiency of serving static files
    """
    dir = skins.utils.get_path_to_skin(skin)
    return static.serve(request, '/media/' + resource, document_root = dir)
