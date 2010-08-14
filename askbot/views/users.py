"""
:synopsis: user-centric views for askbot

This module includes all views that are specific to a given user - his or her profile, 
and other views showing profile-related information.

Also this module includes the view listing all forum users.
"""
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core import mail
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags
from django.utils import simplejson
from django.conf import settings as django_settings
from askbot.utils.html import sanitize_html
from askbot import auth
from askbot import forms
import calendar
import functools
import datetime
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot import models
from askbot.models import signals
import logging

question_type = ContentType.objects.get_for_model(models.Question)
answer_type = ContentType.objects.get_for_model(models.Answer)
comment_type = ContentType.objects.get_for_model(models.Comment)
question_revision_type = ContentType.objects.get_for_model(
                                                models.QuestionRevision
                                            )

answer_revision_type = ContentType.objects.get_for_model(
                                            models.AnswerRevision
                                        )
repute_type = ContentType.objects.get_for_model(models.Repute)
question_type_id = question_type.id
answer_type_id = answer_type.id
comment_type_id = comment_type.id
question_revision_type_id = question_revision_type.id
answer_revision_type_id = answer_revision_type.id
repute_type_id = repute_type.id

def owner_or_moderator_required(f):
    @functools.wraps(f)
    def wrapped_func(request, profile_owner):
        if profile_owner == request.user:
            pass
        elif request.user.is_authenticated() and request.user.can_moderate_user(profile_owner):
            pass
        else:
            raise Http404 #todo: change to access forbidden?
        return f(request, profile_owner)
    return wrapped_func 

def users(request):
    is_paginated = True
    sortby = request.GET.get('sort', 'reputation')
    suser = request.REQUEST.get('q',  "")
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if suser == "":
        if sortby == "newest":
            order_by_parameter = '-date_joined'
        elif sortby == "last":
            order_by_parameter = 'date_joined'
        elif sortby == "user":
            order_by_parameter = 'username'
        else:
            # default
            order_by_parameter = '-reputation'

        objects_list = Paginator(
                            models.User.objects.all().order_by(
                                                order_by_parameter
                                            ), 
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users') + '?sort=%s&' % sortby
    else:
        sortby = "reputation"
        objects_list = Paginator(
                            models.User.objects.extra(
                                                where=['username like %s'],
                                                params=['%' + suser + '%']
                                            ).order_by(
                                                '-reputation'
                                            ), 
                            const.USERS_PAGE_SIZE
                        )
        base_url = reverse('users') + '?name=%s&sort=%s&' % (suser, sortby)

    try:
        users_page = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        users_page = objects_list.page(objects_list.num_pages)

    return render_to_response(
                    'users.html', 
                    {
                        'active_tab': 'users',
                        'users' : users_page,
                        'suser' : suser,
                        'keywords' : suser,
                        'tab_id' : sortby,
                        'context' : {
                            'is_paginated' : is_paginated,
                            'pages': objects_list.num_pages,
                            'page': page,
                            'has_previous': users_page.has_previous(),
                            'has_next': users_page.has_next(),
                            'previous': users_page.previous_page_number(),
                            'next': users_page.next_page_number(),
                            'base_url' : base_url
                        }
                    }, 
                    context_instance=RequestContext(request)
                )

def user_moderate(request, subject):
    """user subview for moderation 
    """
    moderator = request.user

    if not moderator.can_moderate_user(subject):
        raise Http404

    user_rep_changed = False
    user_status_changed = False
    message_sent = False

    user_rep_form = forms.ChangeUserReputationForm()
    send_message_form = forms.SendMessageForm()
    if request.method == 'POST':
        if 'change_status' in request.POST:
            user_status_form = forms.ChangeUserStatusForm(
                                                    request.POST,
                                                    moderator = moderator,
                                                    subject = subject
                                                )
            if user_status_form.is_valid():
                subject.set_status( user_status_form.cleaned_data['user_status'] )
            user_status_changed = True
        elif 'send_message' in request.POST:
            send_message_form = forms.SendMessageForm(request.POST)
            if send_message_form.is_valid():
                subject_line = send_message_form.cleaned_data['subject_line']
                body_text = send_message_form.cleaned_data['body_text']
                message = mail.EmailMessage(
                                    subject_line,
                                    body_text,
                                    django_settings.DEFAULT_FROM_EMAIL,
                                    [subject.email,],
                                    headers={'Reply-to':moderator.email}
                                )
                try:
                    message.send()
                    message_sent = True
                except Exception, e:
                    logging.critical(unicode(e))
                send_message_form = forms.SendMessageForm()
        else:
            reputation_change_type = None
            if 'subtract_reputation' in request.POST:
                rep_change_type = 'subtract'
            elif 'add_reputation' in request.POST:
                rep_change_type = 'add'
            else:
                raise Http404

            user_rep_form = forms.ChangeUserReputationForm(request.POST)
            if user_rep_form.is_valid():
                rep_delta = user_rep_form.cleaned_data['user_reputation_delta']
                comment = user_rep_form.cleaned_data['comment']

                if rep_change_type == 'subtract':
                    rep_delta = -1 * rep_delta

                moderator.moderate_user_reputation(
                                    user = subject,
                                    reputation_change = rep_delta,
                                    comment = comment,
                                    timestamp = datetime.datetime.now(),
                                )
                #reset form to preclude accidentally repeating submission
                user_rep_form = forms.ChangeUserReputationForm()
                user_rep_changed = True

    #need to re-initialize the form even if it was posted, because
    #initial values will most likely be different from the previous
    user_status_form = forms.ChangeUserStatusForm(
                                        moderator = moderator,
                                        subject = subject
                                    )
    return render_to_response(
                    'user_moderate.html',
                    {
                        'active_tab': 'users',
                        'tab_name': 'moderation',
                        'tab_description': _('moderate this user'),
                        'page_title': _('moderate user'),
                        'view_user': subject,
                        'change_user_status_form': user_status_form,
                        'change_user_reputation_form': user_rep_form,
                        'send_message_form': send_message_form,
                        'message_sent': message_sent,
                        'user_rep_changed': user_rep_changed,
                        'user_status_changed': user_status_changed
                    }, 
                    context_instance=RequestContext(request)
                )

#non-view function
def set_new_email(user, new_email, nomessage=False):
    if new_email != user.email:
        user.email = new_email
        user.email_isvalid = False
        user.save()
        #if askbot_settings.EMAIL_VALIDATION == True:
        #    send_new_email_key(user,nomessage=nomessage)    

@login_required
def edit_user(request, id):
    """View that allows to edit user profile.
    This view is accessible to profile owners or site administrators
    """
    user = get_object_or_404(models.User, id=id)
    if not(request.user == user or request.user.is_superuser):
        raise Http404
    if request.method == "POST":
        form = forms.EditUserForm(user, request.POST)
        if form.is_valid():
            new_email = sanitize_html(form.cleaned_data['email'])

            set_new_email(user, new_email)

            if askbot_settings.EDITABLE_SCREEN_NAME:
                user.username = sanitize_html(form.cleaned_data['username'])

            user.real_name = sanitize_html(form.cleaned_data['realname'])
            user.website = sanitize_html(form.cleaned_data['website'])
            user.location = sanitize_html(form.cleaned_data['city'])
            user.date_of_birth = sanitize_html(form.cleaned_data['birthday'])

            if len(user.date_of_birth) == 0:
                user.date_of_birth = '1900-01-01'

            user.about = sanitize_html(form.cleaned_data['about'])

            user.save()
            # send user updated singal if full fields have been updated
            if user.email and user.real_name and user.website \
                and user.location and  user.date_of_birth and user.about:
                signals.user_updated.send(
                                sender=user.__class__, 
                                instance=user, 
                                updated_by=user
                            )
            return HttpResponseRedirect(user.get_profile_url())
    else:
        form = forms.EditUserForm(user)
    return render_to_response(
                        'user_edit.html', 
                        {
                            'active_tab': 'users',
                            'form' : form,
                            'gravatar_faq_url' : reverse('faq') + '#gravatar',
                        }, 
                        context_instance=RequestContext(request)
                    )

def user_stats(request, user):

    questions = models.Question.objects.extra(
        select={
            'score' : 'question.score',
            'favorited_myself' : 'SELECT count(*) FROM favorite_question f WHERE f.user_id = %s AND f.question_id = question.id',
            'la_user_id' : 'auth_user.id',
            'la_username' : 'auth_user.username',
            'la_user_gold' : 'auth_user.gold',
            'la_user_silver' : 'auth_user.silver',
            'la_user_bronze' : 'auth_user.bronze',
            'la_user_reputation' : 'auth_user.reputation'
            },
        select_params=[user.id],
        tables=['question', 'auth_user'],
        where=['question.deleted=False AND question.author_id=%s AND question.last_activity_by_id = auth_user.id'],
        params=[user.id],
        order_by=['-score', '-last_activity_at']
    ).values('score',
             'favorited_myself',
             'id',
             'title',
             'author_id',
             'added_at',
             'answer_accepted',
             'answer_count',
             'comment_count',
             'view_count',
             'favourite_count',
             'summary',
             'tagnames',
             'vote_up_count',
             'vote_down_count',
             'last_activity_at',
             'la_user_id',
             'la_username',
             'la_user_gold',
             'la_user_silver',
             'la_user_bronze',
             'la_user_reputation')[:100]

    #this is meant for the questions answered by the user (or where answers were edited by him/her?)
    answered_questions = models.Question.objects.extra(
        select={
            'vote_up_count' : 'answer.vote_up_count',
            'vote_down_count' : 'answer.vote_down_count',
            'answer_id' : 'answer.id',
            'answer_accepted' : 'answer.accepted',
            'answer_score' : 'answer.score',
            'comment_count' : 'answer.comment_count'
            },
        tables=['question', 'answer'],
        where=['answer.deleted=False AND question.deleted=False AND answer.author_id=%s AND answer.question_id=question.id'],
        params=[user.id],
        order_by=['-answer_score', '-answer_id'],
        select_params=[user.id]
    ).distinct().values('comment_count',
                        'id',
                        'answer_id',
                        'title',
                        'author_id',
                        'answer_accepted',
                        'answer_score',
                        'answer_count',
                        'vote_up_count',
                        'vote_down_count')[:100]

    up_votes = models.Vote.objects.get_up_vote_count_from_user(user)
    down_votes = models.Vote.objects.get_down_vote_count_from_user(user)
    votes_today = models.Vote.objects.get_votes_count_today_from_user(user)
    votes_total = askbot_settings.MAX_VOTES_PER_USER_PER_DAY

    question_id_set = set()
    #todo: there may be a better way to do these queries
    question_id_set.update([q['id'] for q in questions])
    question_id_set.update([q['id'] for q in answered_questions])
    user_tags = models.Tag.objects.filter(questions__id__in = question_id_set)
    try:
        from django.db.models import Count
        #todo - rewrite template to do the table joins within standard ORM
        #awards = models.Award.objects.filter(user=user).order_by('-awarded_at')
        awards = models.Award.objects.extra(
                        select={'id': 'badge.id', 
                                'name':'badge.name', 
                                'description': 'badge.description', 
                                'type': 'badge.type'},
                        tables=['award', 'badge'],
                        order_by=['-awarded_at'],
                        where=['user_id=%s AND badge_id=badge.id'],
                        params=[user.id]
                    ).values('id', 'name', 'description', 'type')

        total_awards = awards.count()
        awards = awards.annotate(count = Count('badge__id'))
        user_tags = user_tags.annotate(user_tag_usage_count=Count('name'))

    except ImportError:
        #todo: remove all old django stuff, e.g. with '.group_by = ' pattern
        awards = models.Award.objects.extra(
                        select={'id': 'badge.id', 
                                'count': 'count(badge_id)', 
                                'name':'badge.name', 
                                'description': 'badge.description', 
                                'type': 'badge.type'},
                        tables=['award', 'badge'],
                        order_by=['-awarded_at'],
                        where=['user_id=%s AND badge_id=badge.id'],
                        params=[user.id]
                    ).values('id', 'count', 'name', 'description', 'type')

        total_awards = awards.count()
        awards.query.group_by = ['badge_id']

        user_tags = user_tags.extra(
            select={'user_tag_usage_count': 'COUNT(1)',},
            order_by=['-user_tag_usage_count'],
        )
        user_tags.query.group_by = ['name']

    if user.is_administrator():
        user_status = _('Site Adminstrator')
    elif user.is_moderator():
        user_status = _('Forum Moderator')
    elif user.is_suspended():
        user_status = _('Suspended User')
    elif user.is_blocked():
        user_status = _('Blocked User')
    else:
        user_status = _('Registered User')

    return render_to_response(
                        'user_stats.html',
                        {
                            'active_tab':'users',
                            'tab_name' : 'stats',
                            'tab_description' : _('user profile'),
                            'page_title' : _('user profile overview'),
                            'view_user' : user,
                            'user_status_for_display': user.get_status_display(soft = True),
                            'questions' : questions,
                            'answered_questions' : answered_questions,
                            'up_votes' : up_votes,
                            'down_votes' : down_votes,
                            'total_votes': up_votes + down_votes,
                            'votes_today_left': votes_total-votes_today,
                            'votes_total_per_day': votes_total,
                            'user_tags' : user_tags[:const.USER_VIEW_DATA_SIZE],
                            'awards': awards,
                            'total_awards' : total_awards,
                        }, 
                        context_instance=RequestContext(request)
                    )

def user_recent(request, user):

    def get_type_name(type_id):
        for item in const.TYPE_ACTIVITY:
            if type_id in item:
                return item[1]

    class Event:
        def __init__(self, time, type, title, summary, answer_id, question_id):
            self.time = time
            self.type = get_type_name(type)
            self.type_id = type
            self.title = title
            self.summary = summary
            slug_title = slugify(title)
            self.title_link = reverse(
                                'question', 
                                kwargs={'id':question_id}
                            ) + u'%s' % slug_title
            if int(answer_id) > 0:
                self.title_link += '#%s' % answer_id

    class AwardEvent:
        def __init__(self, time, type, id):
            self.time = time
            self.type = get_type_name(type)
            self.type_id = type
            self.badge = get_object_or_404(models.Badge, id=id)

    activities = []
    # ask questions
    questions = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'active_at' : 'activity.active_at',
            'activity_type' : 'activity.activity_type'
            },
        tables=['activity', 'question'],
        where=['activity.content_type_id = %s AND activity.object_id = ' +
            'question.id AND question.deleted=False AND activity.user_id = %s AND activity.activity_type = %s'],
        params=[question_type_id, user.id, const.TYPE_ACTIVITY_ASK_QUESTION],
        order_by=['-activity.active_at']
    ).values(
            'title',
            'question_id',
            'active_at',
            'activity_type'
            )
    if len(questions) > 0:

        question_activities = []
        for q in questions:
            q_event = Event(
                        q['active_at'], 
                        q['activity_type'], 
                        q['title'], 
                        '', 
                        '0', 
                        q['question_id']
                    )
            question_activities.append(q_event)

        activities.extend(question_activities)

    # answers
    answers = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'answer_id' : 'answer.id',
            'active_at' : 'activity.active_at',
            'activity_type' : 'activity.activity_type'
            },
        tables=['activity', 'answer', 'question'],
        where=['activity.content_type_id = %s AND activity.object_id = answer.id AND ' + 
            'answer.question_id=question.id AND answer.deleted=False AND activity.user_id=%s AND '+ 
            'activity.activity_type=%s AND question.deleted=False'],
        params=[answer_type_id, user.id, const.TYPE_ACTIVITY_ANSWER],
        order_by=['-activity.active_at']
    ).values(
            'title',
            'question_id',
            'answer_id',
            'active_at',
            'activity_type'
            )
    if len(answers) > 0:
        answers = [(Event(q['active_at'], q['activity_type'], q['title'], '', q['answer_id'], \
                    q['question_id'])) for q in answers]
        activities.extend(answers)

    # question comments
    comments = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'comment.object_id',
            'added_at' : 'comment.added_at',
            'activity_type' : 'activity.activity_type'
            },
        tables=['activity', 'question', 'comment'],

        where=['activity.content_type_id = %s AND activity.object_id = comment.id AND '+
            'activity.user_id = comment.user_id AND comment.object_id=question.id AND '+
            'comment.content_type_id=%s AND activity.user_id = %s AND activity.activity_type=%s AND ' +
            'question.deleted=False'],
        params=[comment_type_id, question_type_id, user.id, const.TYPE_ACTIVITY_COMMENT_QUESTION],
        order_by=['-comment.added_at']
    ).values(
            'title',
            'question_id',
            'added_at',
            'activity_type'
            )

    if len(comments) > 0:
        comments = [(Event(q['added_at'], q['activity_type'], q['title'], '', '0', \
                     q['question_id'])) for q in comments]
        activities.extend(comments)

    # answer comments
    comments = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'answer_id' : 'answer.id',
            'added_at' : 'comment.added_at',
            'activity_type' : 'activity.activity_type'
            },
        tables=['activity', 'question', 'answer', 'comment'],

        where=['activity.content_type_id = %s AND activity.object_id = comment.id AND '+
            'activity.user_id = comment.user_id AND comment.object_id=answer.id AND '+
            'comment.content_type_id=%s AND question.id = answer.question_id AND '+
            'activity.user_id = %s AND activity.activity_type=%s AND '+
            'answer.deleted=False AND question.deleted=False'],
        params=[comment_type_id, answer_type_id, user.id, const.TYPE_ACTIVITY_COMMENT_ANSWER],
        order_by=['-comment.added_at']
    ).values(
            'title',
            'question_id',
            'answer_id',
            'added_at',
            'activity_type'
            )

    if len(comments) > 0:
        comments = [(Event(q['added_at'], q['activity_type'], q['title'], '', q['answer_id'], \
                     q['question_id'])) for q in comments]
        activities.extend(comments)

    # question revisions
    revisions = models.Activity.objects.extra(
        select={
            'title' : 'question_revision.title',
            'question_id' : 'question_revision.question_id',
            'added_at' : 'activity.active_at',
            'activity_type' : 'activity.activity_type',
            'summary' : 'question_revision.summary'
            },
        tables=['activity', 'question_revision', 'question'],
        where=['activity.content_type_id = %s AND activity.object_id = question_revision.id AND '+
            'question_revision.id=question.id AND question.deleted=False AND '+
            'activity.user_id = question_revision.author_id AND activity.user_id = %s AND '+
            'activity.activity_type=%s'],
        params=[question_revision_type_id, user.id, const.TYPE_ACTIVITY_UPDATE_QUESTION],
        order_by=['-activity.active_at']
    ).values(
            'title',
            'question_id',
            'added_at',
            'activity_type',
            'summary'
            )

    if len(revisions) > 0:
        revisions = [(Event(q['added_at'], q['activity_type'], q['title'], q['summary'], '0', \
                      q['question_id'])) for q in revisions]
        activities.extend(revisions)

    # answer revisions
    revisions = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'answer_id' : 'answer.id',
            'added_at' : 'activity.active_at',
            'activity_type' : 'activity.activity_type',
            'summary' : 'answer_revision.summary'
            },
        tables=['activity', 'answer_revision', 'question', 'answer'],

        where=['activity.content_type_id = %s AND activity.object_id = answer_revision.id AND '+
            'activity.user_id = answer_revision.author_id AND activity.user_id = %s AND '+
            'answer_revision.answer_id=answer.id AND answer.question_id = question.id AND '+
            'question.deleted=False AND answer.deleted=False AND '+
            'activity.activity_type=%s'],
        params=[answer_revision_type_id, user.id, const.TYPE_ACTIVITY_UPDATE_ANSWER],
        order_by=['-activity.active_at']
    ).values(
            'title',
            'question_id',
            'added_at',
            'answer_id',
            'activity_type',
            'summary'
            )

    if len(revisions) > 0:
        revisions = [(Event(q['added_at'], q['activity_type'], q['title'], q['summary'], \
                      q['answer_id'], q['question_id'])) for q in revisions]
        activities.extend(revisions)

    # accepted answers
    accept_answers = models.Activity.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'added_at' : 'activity.active_at',
            'activity_type' : 'activity.activity_type',
            },
        tables=['activity', 'answer', 'question'],
        where=['activity.content_type_id = %s AND activity.object_id = answer.id AND '+
            'activity.user_id = question.author_id AND activity.user_id = %s AND '+
            'answer.deleted=False AND question.deleted=False AND '+
            'answer.question_id=question.id AND activity.activity_type=%s'],
        params=[answer_type_id, user.id, const.TYPE_ACTIVITY_MARK_ANSWER],
        order_by=['-activity.active_at']
    ).values(
            'title',
            'question_id',
            'added_at',
            'activity_type',
            )
    if len(accept_answers) > 0:
        accept_answers = [(Event(q['added_at'], q['activity_type'], q['title'], '', '0', \
            q['question_id'])) for q in accept_answers]
        activities.extend(accept_answers)
    #award history
    awards = models.Activity.objects.extra(
        select={
            'badge_id' : 'badge.id',
            'awarded_at': 'award.awarded_at',
            'activity_type' : 'activity.activity_type'
            },
        tables=['activity', 'award', 'badge'],
        where=['activity.user_id = award.user_id AND activity.user_id = %s AND '+
            'award.badge_id=badge.id AND activity.object_id=award.id AND activity.activity_type=%s'],
        params=[user.id, const.TYPE_ACTIVITY_PRIZE],
        order_by=['-activity.active_at']
    ).values(
            'badge_id',
            'awarded_at',
            'activity_type'
            )
    if len(awards) > 0:
        awards = [(AwardEvent(q['awarded_at'], q['activity_type'], q['badge_id'])) for q in awards]
        activities.extend(awards)

    activities.sort(lambda x,y: cmp(y.time, x.time))

    return render_to_response('user_recent.html',
                                 {
                                    'active_tab': 'users',
                                    "tab_name" : 'recent',
                                    "tab_description" : _('recent user activity'),
                                    "page_title" : _('profile - recent activity'),
                                    "view_user" : user,
                                    "activities" : activities[:const.USER_VIEW_DATA_SIZE]
                                }, context_instance=RequestContext(request))

#class Response:
#    """class that abstracts any kind of response
#    answer, comment, mention, post edits, etc.
#    """
#    def __init__(
#            self, type, title, question_id, 
#            answer_id, time, username, 
#            user_id, content):
#
#        self.type = type
#        self.title = title
#        self.titlelink = reverse(
#                            'question', 
#                            args=[question_id]) \
#                                    + u'%s#%s' % (slugify(title), 
#                            answer_id
#                        )
#        self.time = time
#        self.userlink = reverse('users') + u'%s/%s/' % (user_id, username)
#        self.username = username
#        self.content = u'%s ...' % strip_tags(content)[:300]

#    def __unicode__(self):
#        return u'%s %s' % (self.type, self.titlelink)

@owner_or_moderator_required
def user_responses(request, user):
    """
    We list answers for question, comments, and 
    answer accepted by others for this user.
    as well as mentions of the user

    user - the profile owner
    """

    response_list = []

    activities = list()
    activities = models.Activity.responses_and_mentions.filter(
                                                        receiving_users = user
                                                    )

    for act in activities:
        origin_post = act.content_object.get_origin_post()
        response = {
            'timestamp': act.active_at,
            'user': act.user,
            'response_url': act.get_absolute_url(),
            'response_snippet': strip_tags(act.content_object.html)[:300],
            'response_title': origin_post.title,
            'response_type': act.get_activity_type_display(),
        }
        response_list.append(response)

    response_list.sort(lambda x,y: cmp(y['timestamp'], x['timestamp']))

    return render_to_response(
                    'user_responses.html',
                    {
                        'active_tab':'users',
                        'tab_name' : 'responses',
                        'tab_description' : _('comments and answers to others questions'),
                        'page_title' : _('profile - responses'),
                        'view_user' : user,
                        'responses' : response_list[:const.USER_VIEW_DATA_SIZE],
                    }, 
                    context_instance=RequestContext(request)
                )

@owner_or_moderator_required
def user_votes(request, user):

    votes = []
    question_votes = models.Vote.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'answer_id' : 0,
            'voted_at' : 'vote.voted_at',
            'vote' : 'vote',
            },
        select_params=[user.id],
        tables=['vote', 'question', 'auth_user'],
        where=['vote.content_type_id = %s AND vote.user_id = %s AND vote.object_id = question.id '+
            'AND vote.user_id=auth_user.id'],
        params=[question_type_id, user.id],
        order_by=['-vote.id']
    ).values(
            'title',
            'question_id',
            'answer_id',
            'voted_at',
            'vote',
            )
    if(len(question_votes) > 0):
        votes.extend(question_votes)

    answer_votes = models.Vote.objects.extra(
        select={
            'title' : 'question.title',
            'question_id' : 'question.id',
            'answer_id' : 'answer.id',
            'voted_at' : 'vote.voted_at',
            'vote' : 'vote',
            },
        select_params=[user.id],
        tables=['vote', 'answer', 'question', 'auth_user'],
        where=['vote.content_type_id = %s AND vote.user_id = %s AND vote.object_id = answer.id '+
            'AND answer.question_id = question.id AND vote.user_id=auth_user.id'],
        params=[answer_type_id, user.id],
        order_by=['-vote.id']
    ).values(
            'title',
            'question_id',
            'answer_id',
            'voted_at',
            'vote',
            )
    if(len(answer_votes) > 0):
        votes.extend(answer_votes)
    votes.sort(lambda x,y: cmp(y['voted_at'], x['voted_at']))

    return render_to_response('user_votes.html', {
        'active_tab':'users',
        "tab_name" : 'votes',
        "tab_description" : _('user vote record'),
        "page_title" : _('profile - votes'),
        "view_user" : user,
        "votes" : votes[:const.USER_VIEW_DATA_SIZE]
    }, context_instance=RequestContext(request))

def user_reputation(request, user):
    reputes = models.Repute.objects.filter(user=user).order_by('-reputed_at')
    #select_related() adds stuff needed for the query
    reputes = reputes.select_related(
                            'question__title', 
                            'question__id', 
                            'user__username'
                        )
    #reputes = reputates.annotate(positive=Sum("positive"), negative=Sum("negative"))

    #prepare data for the graph
    rep_list = []
    #last values go in first
    rep_list.append('[%s,%s]' % (
                            calendar.timegm(
                                        datetime.datetime.now().timetuple()
                                    ) * 1000,
                            user.reputation
                        )
                    )
    #ret remaining values in
    for rep in reputes:
        dic = '[%s,%s]' % (calendar.timegm(rep.reputed_at.timetuple()) * 1000, rep.reputation)
        rep_list.append(dic)
    reps = ','.join(rep_list)
    reps = '[%s]' % reps

    return render_to_response('user_reputation.html', {
                              'active_tab':'users',
                              "tab_name": 'reputation',
                              "tab_description": _('user reputation in the community'),
                              "page_title": _('profile - user reputation'),
                              "view_user": user,
                              "reputation": reputes,
                              "reps": reps
                              }, context_instance=RequestContext(request))

def user_favorites(request, user):
    questions = models.Question.objects.extra(
        select={
            'score' : 'question.vote_up_count + question.vote_down_count',
            'favorited_myself' : 'SELECT count(*) FROM favorite_question f WHERE f.user_id = %s '+
                'AND f.question_id = question.id',
            'la_user_id' : 'auth_user.id',
            'la_username' : 'auth_user.username',
            'la_user_gold' : 'auth_user.gold',
            'la_user_silver' : 'auth_user.silver',
            'la_user_bronze' : 'auth_user.bronze',
            'la_user_reputation' : 'auth_user.reputation'
            },
        select_params=[user.id],
        tables=['question', 'auth_user', 'favorite_question'],
        where=['question.deleted=False AND question.last_activity_by_id = auth_user.id '+
            'AND favorite_question.question_id = question.id AND favorite_question.user_id = %s'],
        params=[user.id],
        order_by=['-score', '-question.id']
    ).values('score',
             'favorited_myself',
             'id',
             'title',
             'author_id',
             'added_at',
             'answer_accepted',
             'answer_count',
             'comment_count',
             'view_count',
             'favourite_count',
             'summary',
             'tagnames',
             'vote_up_count',
             'vote_down_count',
             'last_activity_at',
             'la_user_id',
             'la_username',
             'la_user_gold',
             'la_user_silver',
             'la_user_bronze',
             'la_user_reputation')

    return render_to_response('user_favorites.html',{
        'active_tab':'users',
        "tab_name" : 'favorites',
        "tab_description" : _('users favorite questions'),
        "page_title" : _('profile - favorite questions'),
        "questions" : questions[:const.USER_VIEW_DATA_SIZE],
        "view_user" : user
    }, context_instance=RequestContext(request))

@owner_or_moderator_required
def user_email_subscriptions(request, user):

    if request.method == 'POST':
        email_feeds_form = forms.EditUserEmailFeedsForm(request.POST)
        tag_filter_form = forms.TagFilterSelectionForm(request.POST, instance=user)
        if email_feeds_form.is_valid() and tag_filter_form.is_valid():

            action_status = None
            tag_filter_saved = tag_filter_form.save()
            if tag_filter_saved:
                action_status = _('changes saved')
            if 'save' in request.POST:
                feeds_saved = email_feeds_form.save(user)
                if feeds_saved:
                    action_status = _('changes saved')
            elif 'stop_email' in request.POST:
                email_stopped = email_feeds_form.reset().save(user)
                initial_values = forms.EditUserEmailFeedsForm.NO_EMAIL_INITIAL
                email_feeds_form = forms.EditUserEmailFeedsForm(initial=initial_values)
                if email_stopped:
                    action_status = _('email updates canceled')
    else:
        email_feeds_form = forms.EditUserEmailFeedsForm()
        email_feeds_form.set_initial_values(user)
        tag_filter_form = forms.TagFilterSelectionForm(instance=user)
        action_status = None

    return render_to_response('user_email_subscriptions.html',{
        'active_tab': 'users',
        'tab_name': 'email_subscriptions',
        'tab_description': _('email subscription settings'),
        'page_title': _('profile - email subscriptions'),
        'view_user': user,
        'email_feeds_form': email_feeds_form,
        'tag_filter_selection_form': tag_filter_form,
        'action_status': action_status,
    }, context_instance=RequestContext(request))

user_view_call_table = {
    'stats': user_stats,
    'recent': user_recent,
    'responses': user_responses,
    'reputation': user_reputation,
    'favorites': user_favorites,
    'votes': user_votes,
    'email_subscriptions': user_email_subscriptions,
    'moderation': user_moderate,
}
#todo: rename this function - variable named user is everywhere
def user(request, id, slug=None):
    """Main user view function that works as a switchboard

    id - id of the profile owner

    todo: decide what to do with slug - it is not used
    in the code in any way
    """

    profile_owner = get_object_or_404(models.User, id = id)

    #sort CGI parameter tells us which tab in the user
    #profile to show, the default one is 'stats'
    tab_name = request.GET.get('sort', 'stats')

    if tab_name in user_view_call_table:
        #get the actual view function
        user_view_func = user_view_call_table[tab_name]
    else:
        user_view_func = user_stats

    return user_view_func(request, profile_owner)

@login_required
def account_settings(request):#todo: is this actually used?
    """
    index pages to changes some basic account settings :
     - change password
     - change email
     - associate a new openid
     - delete account

    url : /

    template : authopenid/settings.html
    """
    logging.debug('')
    msg = request.GET.get('msg', '')
    is_openid = False

    return render_to_response('account_settings.html', {
        'active_tab':'users',
        'msg': msg,
        'is_openid': is_openid
        }, context_instance=RequestContext(request))

