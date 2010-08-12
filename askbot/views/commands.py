"""
:synopsis: most ajax processors for askbot

This module contains most (but not all) processors for Ajax requests. 
Not so clear if this subdivision was necessary as separation of Ajax and non-ajax views
is not always very clean.
"""
import datetime
#todo: maybe eliminate usage of django.settings
from django.conf import settings
from askbot.conf import settings as askbot_settings
from django.utils import simplejson
from django.core import exceptions
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from askbot.models import * #todo: clean this up
from askbot.forms import CloseForm
from askbot import auth
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from askbot.utils.decorators import ajax_method, ajax_login_required
from askbot.templatetags import extra_filters as template_filters
import logging

def process_vote(user = None, vote_direction = None, post = None):
    """function (non-view) that actually processes user votes
    - i.e. up- or down- votes

    in the future this needs to be converted into a real view function
    for that url and javascript will need to be adjusted

    also in the future make keys in response data be more meaningful
    right now they are kind of cryptic - "status", "count"
    """

    if user.is_anonymous():
        raise exceptions.PermissionDenied(_('anonymous users cannot vote'))

    user.assert_can_vote_for_post(
                                    post = post, 
                                    direction = vote_direction
                                )

    vote = user.get_old_vote_for_post(post)
    response_data = {}
    if vote != None:
        user.assert_can_revoke_old_vote(vote)
        score_delta = vote.cancel()
        response_data['count'] = post.score + score_delta
        response_data['status'] = 1 #this means "cancel"

    else:
        #this is a new vote
        votes_left = user.get_unused_votes_today()
        if votes_left <= 0:
            raise exceptions.PermissionDenied(
                            _('Sorry you ran out of votes for today')
                        )

        votes_left -= 1
        if votes_left <= \
            askbot_settings.VOTES_LEFT_WARNING_THRESHOLD:
            msg = _('You have %(votes_left)s votes left for today') \
                    % {'votes_left': votes_left }
            response_data['message'] = msg

        if vote_direction == 'up':
            vote = user.upvote(post = post)
        else:
            vote = user.downvote(post = post)

        response_data['count'] = post.score 
        response_data['status'] = 0 #this means "not cancel", normal operation

    response_data['success'] = 1

    return response_data


def vote(request, id):
    """
    todo: this subroutine needs serious refactoring it's too long and is hard to understand

    vote_type:
        acceptAnswer : 0,
        questionUpVote : 1,
        questionDownVote : 2,
        favorite : 4,
        answerUpVote: 5,
        answerDownVote:6,
        offensiveQuestion : 7,
        offensiveAnswer:8,
        removeQuestion: 9,
        removeAnswer:10
        questionSubscribeUpdates:11
        questionUnSubscribeUpdates:12

    accept answer code:
        response_data['allowed'] = -1, Accept his own answer   0, no allowed - Anonymous    1, Allowed - by default
        response_data['success'] =  0, failed                                               1, Success - by default
        response_data['status']  =  0, By default                       1, Answer has been accepted already(Cancel)

    vote code:
        allowed = -3, Don't have enough votes left
                  -2, Don't have enough reputation score
                  -1, Vote his own post
                   0, no allowed - Anonymous
                   1, Allowed - by default
        status  =  0, By default
                   1, Cancel
                   2, Vote is too old to be canceled

    offensive code:
        allowed = -3, Don't have enough flags left
                  -2, Don't have enough reputation score to do this
                   0, not allowed
                   1, allowed
        status  =  0, by default
                   1, can't do it again
    """
    response_data = {
        "allowed": 1,
        "success": 1,
        "status" : 0,
        "count"  : 0,
        "message" : ''
    }

    try:
        if request.is_ajax() and request.method == 'POST':
            vote_type = request.POST.get('type')
        else:
            raise Exception(_('Sorry, something is not right here...'))

        if vote_type == '0':
            if request.user.is_authenticated():
                answer_id = request.POST.get('postId')
                answer = get_object_or_404(Answer, id = answer_id)
                question = answer.question
                # make sure question author is current user
                if answer.accepted:
                    request.user.unaccept_best_answer(answer)
                    response_data['status'] = 1 #cancelation
                else:
                    request.user.accept_best_answer(answer)
            else:
                raise exceptions.PermissionDenied(
                        _('Sorry, but anonymous users cannot accept answers')
                    )

        elif vote_type in ('1', '2', '5', '6'):#Q&A up/down votes

            ###############################
            # all this can be avoided with
            # better query parameters
            vote_direction = 'up'
            if vote_type in ('2','6'):
                vote_direction = 'down'

            if vote_type in ('5', '6'):
                #todo: fix this weirdness - why postId here 
                #and not with question?
                id = request.POST.get('postId')
                post = get_object_or_404(Answer, id=id)
            else:
                post = get_object_or_404(Question, id=id)
            #
            ######################

            response_data = process_vote(
                                        user = request.user,
                                        vote_direction = vote_direction,
                                        post = post
                                    )

        elif vote_type in ['7', '8']:
            #flag question or answer
            if vote_type == '7':
                post = get_object_or_404(Question, id=id)
            if vote_type == '8':
                id = request.POST.get('postId')
                post = get_object_or_404(Answer, id=id)

            request.user.flag_post(post)

            response_data['count'] = post.offensive_flag_count
            response_data['success'] = 1

        elif vote_type in ['9', '10']:
            #delete question or answer
            post = get_object_or_404(Question, id = id) 
            if vote_type == '10':
                id = request.POST.get('postId')
                post = get_object_or_404(Answer, id = id)

            if post.deleted == True:
                request.user.restore_post(post = post)
            else:
                request.user.delete_post(post = post)

        elif request.is_ajax() and request.method == 'POST':

            if not request.user.is_authenticated():
                response_data['allowed'] = 0
                response_data['success'] = 0

            question = get_object_or_404(Question, id=id)
            vote_type = request.POST.get('type')

            #accept answer
            if vote_type == '4':
                has_favorited = False
                fave = request.user.toggle_favorite_question(question)
                response_data['count'] = FavoriteQuestion.objects.filter(
                                            question = question
                                        ).count()
                if fave == False:
                    response_data['status'] = 1

            elif vote_type == '11':#subscribe q updates
                user = request.user
                if user.is_authenticated():
                    if user not in question.followed_by.all():
                        user.follow_question(question)
                        if askbot_settings.EMAIL_VALIDATION == True \
                            and user.email_isvalid == False:

                            response_data['message'] = \
                                    _('subscription saved, %(email)s needs validation, see %(details_url)s') \
                                    % {'email':user.email,'details_url':reverse('faq') + '#validate'}
                    feed_setting = EmailFeedSetting.objects.get(subscriber=user,feed_type='q_sel')
                    if feed_setting.frequency == 'n':
                        feed_setting.frequency = 'd'
                        feed_setting.save()
                        if 'message' in response_data:
                            response_data['message'] += '<br/>'
                        response_data['message'] = _('email update frequency has been set to daily')
                    #response_data['status'] = 1
                    #responst_data['allowed'] = 1
                else:
                    pass
                    #response_data['status'] = 0
                    #response_data['allowed'] = 0
            elif vote_type == '12':#unsubscribe q updates
                user = request.user
                if user.is_authenticated():
                    user.unfollow_question(question)
        else:
            response_data['success'] = 0
            response_data['message'] = u'Request mode is not supported. Please try again.'

        data = simplejson.dumps(response_data)

    except Exception, e:
        response_data['message'] = unicode(e)
        response_data['success'] = 0
        data = simplejson.dumps(response_data)
    return HttpResponse(data, mimetype="application/json")

#internally grouped views - used by the tagging system
@ajax_login_required
def mark_tag(request, tag=None, **kwargs):#tagging system
    action = kwargs['action']
    ts = MarkedTag.objects.filter(user=request.user, tag__name=tag)
    if action == 'remove':
        logging.debug('deleting tag %s' % tag)
        ts.delete()
    else:
        reason = kwargs['reason']
        if len(ts) == 0:
            try:
                t = Tag.objects.get(name=tag)
                mt = MarkedTag(user=request.user, reason=reason, tag=t)
                mt.save()
            except:
                pass
        else:
            ts.update(reason=reason)
    return HttpResponse(simplejson.dumps(''), mimetype="application/json")

@ajax_login_required
def ajax_toggle_ignored_questions(request):#ajax tagging and tag-filtering system
    if request.user.hide_ignored_questions:
        new_hide_setting = False
    else:
        new_hide_setting = True
    request.user.hide_ignored_questions = new_hide_setting
    request.user.save()

@ajax_method
def ajax_command(request):
    """view processing ajax commands - note "vote" and view others do it too
    """
    if 'command' not in request.POST:
        return HttpResponseForbidden(mimetype="application/json")
    if request.POST['command'] == 'toggle-ignored-questions':
        return ajax_toggle_ignored_questions(request)

@login_required
def close(request, id):#close question
    """view to initiate and process 
    question close
    """
    question = get_object_or_404(Question, id=id)
    try:
        if request.method == 'POST':
            form = CloseForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data['reason']

                request.user.close_question(
                                        question = question,
                                        reason = reason
                                    )
            return HttpResponseRedirect(question.get_absolute_url())
        else:
            request.user.assert_can_close_question(question)
            form = CloseForm()
            response = render_to_response(
                            'close.html', 
                            {
                                'form' : form,
                                'question' : question,
                            }, 
                            context_instance=RequestContext(request)
                        )
            return response
    except exceptions.PermissionDenied, e:
        request.user.message_set.create(message = unicode(e))
        return HttpResponseRedirect(question.get_absolute_url())

@login_required
def reopen(request, id):#re-open question
    """view to initiate and process 
    question close

    this is not an ajax view
    """

    question = get_object_or_404(Question, id=id)
    # open question
    try:
        if request.method == 'POST' :
            request.user.reopen_question(question)
            return HttpResponseRedirect(question.get_absolute_url())
        else:
            request.user.assert_can_reopen_question(question)
            closed_by_profile_url = question.closed_by.get_profile_url()
            closed_by_username = question.closed_by.username
            return render_to_response(
                            'reopen.html', 
                            {
                                'question' : question,
                                'closed_by_profile_url': closed_by_profile_url,
                                'closed_by_username': closed_by_username,
                            },
                            context_instance=RequestContext(request)
                        )
    except exceptions.PermissionDenied, e:
        request.user.message_set.create(message = unicode(e))
        return HttpResponseRedirect(question.get_absolute_url())

#askbot-user communication system
def read_message(request):#marks message a read
    if request.method == "POST":
        if request.POST['formdata'] == 'required':
            request.session['message_silent'] = 1
            if request.user.is_authenticated():
                request.user.delete_messages()
    return HttpResponse('')
