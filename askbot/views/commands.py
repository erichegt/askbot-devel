"""
:synopsis: most ajax processors for askbot

This module contains most (but not all) processors for Ajax requests. 
Not so clear if this subdivision was necessary as separation of Ajax and non-ajax views
is not always very clean.
"""
from askbot.conf import settings as askbot_settings
from django.utils import simplejson
from django.core import exceptions
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext
from askbot import models
from askbot.forms import CloseForm
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from askbot.utils.decorators import ajax_only, ajax_login_required
from askbot.skins.loaders import ENV
from askbot import const
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

def manage_inbox(request):
    """delete, mark as new or seen user's
    response memo objects, excluding flags
    request data is memo_list  - list of integer id's of the ActivityAuditStatus items
    and action_type - string - one of delete|mark_new|mark_seen
    """

    response_data = dict()
    try:
        if request.is_ajax():
            if request.method == 'POST':
                post_data = simplejson.loads(request.raw_post_data)
                if request.user.is_authenticated():
                    activity_types = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
                    activity_types += (const.TYPE_ACTIVITY_MENTION, )
                    user = request.user
                    memo_set = models.ActivityAuditStatus.objects.filter(
                                    id__in = post_data['memo_list'],
                                    activity__activity_type__in = activity_types,
                                    user = user
                                )
                    action_type = post_data['action_type']
                    seen_memos = memo_set.filter(
                                    status=models.ActivityAuditStatus.STATUS_SEEN
                                )
                    new_memos = memo_set.filter(
                                    status=models.ActivityAuditStatus.STATUS_NEW
                                )
                    if action_type == 'delete':
                        user.new_response_count -= new_memos.count()
                        user.seen_response_count -= seen_memos.count()
                        user.clean_response_counts()
                        user.save()
                        memo_set.delete()
                    elif action_type == 'mark_new':
                        user.new_response_count += seen_memos.count()
                        user.seen_response_count -= seen_memos.count()
                        user.clean_response_counts()
                        user.save()
                        memo_set.update(status = models.ActivityAuditStatus.STATUS_NEW)
                    elif action_type == 'mark_seen':
                        user.new_response_count -= new_memos.count()
                        user.seen_response_count += new_memos.count()
                        user.clean_response_counts()
                        user.save()
                        memo_set.update(status = models.ActivityAuditStatus.STATUS_SEEN)
                    else:
                        raise exceptions.PermissionDenied(
                                    _('Oops, apologies - there was some error')
                                )
                    response_data['success'] = True
                    data = simplejson.dumps(response_data)
                    return HttpResponse(data, mimetype="application/json")
                else:
                    raise exceptions.PermissionDenied(
                            _('Sorry, but anonymous users cannot access the inbox')
                        )
            else:
                raise exceptions.PermissionDenied('must use POST request')
        else:
            #todo: show error page but no-one is likely to get here
            return HttpResponseRedirect(reverse('index'))
    except Exception, e:
        message = unicode(e)
        if message == '':
            message = _('Oops, apologies - there was some error')
        response_data['message'] = message
        response_data['success'] = False
        data = simplejson.dumps(response_data)
        return HttpResponse(data, mimetype="application/json")


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
                answer = get_object_or_404(models.Answer, id = answer_id)
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
                post = get_object_or_404(models.Answer, id=id)
            else:
                post = get_object_or_404(models.Question, id=id)
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
                post = get_object_or_404(models.Question, id=id)
            if vote_type == '8':
                id = request.POST.get('postId')
                post = get_object_or_404(models.Answer, id=id)

            request.user.flag_post(post)

            response_data['count'] = post.offensive_flag_count
            response_data['success'] = 1

        elif vote_type in ['9', '10']:
            #delete question or answer
            post = get_object_or_404(models.Question, id = id) 
            if vote_type == '10':
                id = request.POST.get('postId')
                post = get_object_or_404(models.Answer, id = id)

            if post.deleted == True:
                request.user.restore_post(post = post)
            else:
                request.user.delete_post(post = post)

        elif request.is_ajax() and request.method == 'POST':

            if not request.user.is_authenticated():
                response_data['allowed'] = 0
                response_data['success'] = 0

            question = get_object_or_404(models.Question, id=id)
            vote_type = request.POST.get('type')

            #accept answer
            if vote_type == '4':
                has_favorited = False
                fave = request.user.toggle_favorite_question(question)
                response_data['count'] = models.FavoriteQuestion.objects.filter(
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
                    feed_setting = models.EmailFeedSetting.objects.get(subscriber=user,feed_type='q_sel')
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
def mark_tag(request, **kwargs):#tagging system
    action = kwargs['action']
    post_data = simplejson.loads(request.raw_post_data)
    tagnames = post_data['tagnames']
    marked_ts = models.MarkedTag.objects.filter(
                                    user=request.user,
                                    tag__name__in=tagnames
                                )
    #todo: use the user api methods here instead of the straight ORM
    if action == 'remove':
        logging.debug('deleting tag marks: %s' % ','.join(tagnames))
        marked_ts.delete()
    else:
        reason = kwargs['reason']
        if len(marked_ts) == 0:
            try:
                ts = models.Tag.objects.filter(name__in=tagnames)
                for tag in ts:
                    mt = models.MarkedTag(
                                user=request.user,
                                reason=reason,
                                tag=tag
                            )
                    mt.save()
            except:
                pass
        else:
            marked_ts.update(reason=reason)
    return HttpResponse(simplejson.dumps(''), mimetype="application/json")

@ajax_login_required
def ajax_toggle_ignored_questions(request):#ajax tagging and tag-filtering system
    if request.user.hide_ignored_questions:
        new_hide_setting = False
    else:
        new_hide_setting = True
    request.user.hide_ignored_questions = new_hide_setting
    request.user.save()

@ajax_only
def ajax_command(request):
    """view processing ajax commands - note "vote" and view others do it too
    """
    if 'command' not in request.POST:
        raise exceptions.PermissionDenied(_('Bad request'))
    if request.POST['command'] == 'toggle-ignored-questions':
        return ajax_toggle_ignored_questions(request)

@login_required
def close(request, id):#close question
    """view to initiate and process 
    question close
    """
    question = get_object_or_404(models.Question, id=id)
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
            template = ENV.get_template('close.html')
            data = {'form': form, 'question': question}
            context = RequestContext(request, data)
            return HttpResponse(template.render(context))
    except exceptions.PermissionDenied, e:
        request.user.message_set.create(message = unicode(e))
        return HttpResponseRedirect(question.get_absolute_url())

@login_required
def reopen(request, id):#re-open question
    """view to initiate and process 
    question close

    this is not an ajax view
    """

    question = get_object_or_404(models.Question, id=id)
    # open question
    try:
        if request.method == 'POST' :
            request.user.reopen_question(question)
            return HttpResponseRedirect(question.get_absolute_url())
        else:
            request.user.assert_can_reopen_question(question)
            closed_by_profile_url = question.closed_by.get_profile_url()
            closed_by_username = question.closed_by.username
            data = {
                'question' : question,
                'closed_by_profile_url': closed_by_profile_url,
                'closed_by_username': closed_by_username,
            }
            context = RequestContext(request, data)
            template = ENV.get_template('reopen.html')
            return HttpResponse(template.render(context))
            
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
