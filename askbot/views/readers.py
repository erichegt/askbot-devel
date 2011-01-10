# encoding:utf-8
"""
:synopsis: views "read-only" for main textual content

By main textual content is meant - text of Questions, Answers and Comments.
The "read-only" requirement here is not 100% strict, as for example "question" view does
allow adding new comments via Ajax form post.
"""
import datetime
import logging
import urllib
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext, Context
from django.utils.http import urlencode
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils import translation
from django.core.urlresolvers import reverse
from django.core import exceptions as django_exceptions
from django.contrib.humanize.templatetags import humanize

import askbot
from askbot import exceptions
from askbot.utils.diff import textDiff as htmldiff
from askbot.forms import AdvancedSearchForm, AnswerForm, ShowQuestionForm
from askbot import models
from askbot.models.badges import award_badges_signal
from askbot import const
from askbot.utils import functions
from askbot.utils.decorators import anonymous_forbidden, ajax_only, get_only
from askbot.search.state_manager import SearchState
from askbot.templatetags import extra_tags
from askbot.templatetags import extra_filters
import askbot.conf
from askbot.skins.loaders import ENV #jinja2 template loading enviroment

# used in index page
#todo: - take these out of const or settings
INDEX_PAGE_SIZE = 30
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 25
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in questions
# used in answers

#system to display main content
def _get_tags_cache_json():#service routine used by views requiring tag list in the javascript space
    """returns list of all tags in json format
    no caching yet, actually
    """
    tags = models.Tag.objects.filter(deleted=False).all()
    tags_list = []
    for tag in tags:
        dic = {'n': tag.name, 'c': tag.used_count}
        tags_list.append(dic)
    tags = simplejson.dumps(tags_list)
    return tags

#refactor? - we have these
#views that generate a listing of questions in one way or another:
#index, unanswered, questions, search, tag
#should we dry them up?
#related topics - information drill-down, search refinement

def index(request):#generates front page - shows listing of questions sorted in various ways
    """index view mapped to the root url of the Q&A site
    """
    return HttpResponseRedirect(reverse('questions'))

def questions(request):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """
    #don't allow to post to this view
    if request.method == 'POST':
        raise Http404

    #todo: redo SearchState to accept input from
    #view_log, session and request parameters
    search_state = request.session.get('search_state', SearchState())

    view_log = request.session['view_log']

    if view_log.get_previous(1) != 'questions':
        if view_log.get_previous(2) != 'questions':
            #print 'user stepped too far, resetting search state'
            search_state.reset()

    if request.user.is_authenticated():
        search_state.set_logged_in()

    form = AdvancedSearchForm(request.GET)
    #todo: form is used only for validation...
    if form.is_valid():
        search_state.update_from_user_input(
                                    form.cleaned_data,
                                    request.GET,
                                )
        #todo: better put these in separately then analyze
        #what neesd to be done, otherwise there are two routines
        #that take request.GET I don't like this use of parameters
        #another weakness is that order of routine calls matters here
        search_state.relax_stickiness( request.GET, view_log )

        request.session['search_state'] = search_state
        request.session.modified = True

    #force reset for debugging
    #search_state.reset()
    #request.session.modified = True

    #todo: have this call implemented for sphinx, mysql and pgsql
    (qs, meta_data, related_tags) = models.Question.objects.run_advanced_search(
                                            request_user = request.user,
                                            search_state = search_state,
                                        )

    paginator = Paginator(qs, search_state.page_size)

    if paginator.num_pages < search_state.page:
        raise Http404

    page = paginator.page(search_state.page)

    contributors = models.Question.objects.get_question_and_answer_contributors(page.object_list)

    paginator_context = {
        'is_paginated' : (paginator.count > search_state.page_size),
        'pages': paginator.num_pages,
        'page': search_state.page,
        'has_previous': page.has_previous(),
        'has_next': page.has_next(),
        'previous': page.previous_page_number(),
        'next': page.next_page_number(),
        'base_url' : request.path + '?sort=%s&amp;' % search_state.sort,#todo in T sort=>sort_method
        'page_size' : search_state.page_size,#todo in T pagesize -> page_size
    }

    if request.is_ajax():

        q_count = paginator.count
        question_counter = ungettext(
                                '%(q_num)s question',
                                '%(q_num)s questions',
                                q_count
                            ) % {
                                'q_num': humanize.intcomma(q_count),
                            }

        if q_count > search_state.page_size:
            paginator_tpl = ENV.get_template('blocks/paginator.html')
            #todo: remove this patch on context after all templates are moved to jinja
            paginator_context['base_url'] = request.path + '?sort=%s&' % search_state.sort
            data = {
                'paginator_context': extra_tags.cnprog_paginator(paginator_context)
            }
            paginator_html = paginator_tpl.render(Context(data))
        else:
            paginator_html = ''
        ajax_data = {
            #current page is 1 by default now
            #because ajax is only called by update in the search button
            'paginator': paginator_html,
            'question_counter': question_counter,
            'questions': list(),
            'related_tags': list(),
            'faces': list()
        }

        badge_levels = dict(const.BADGE_TYPE_CHOICES)
        def pluralize_badge_count(count, level):
            return ungettext(
                '%(badge_count)d %(badge_level)s badge',
                '%(badge_count)d %(badge_level)s badges',
                count
            ) % {
                'badge_count': count, 
                'badge_level': badge_levels[level]
            }

        gold_badge_css_class = const.BADGE_CSS_CLASSES[const.GOLD_BADGE],
        silver_badge_css_class = const.BADGE_CSS_CLASSES[const.SILVER_BADGE],
        bronze_badge_css_class = const.BADGE_CSS_CLASSES[const.BRONZE_BADGE],

        for tag in related_tags:
            tag_data = {
                'name': tag.name,
                'used_count': humanize.intcomma(tag.local_used_count)
            }
            ajax_data['related_tags'].append(tag_data)

        for contributor in contributors:
            ajax_data['faces'].append(extra_tags.gravatar(contributor, 48))

        for question in page.object_list:
            timestamp = question.last_activity_at
            author = question.last_activity_by

            if question.score == 0:
                votes_class = 'no-votes'
            else:
                votes_class = 'some-votes'

            if question.answer_count == 0:
                answers_class = 'no-answers'
            elif question.answer_accepted:
                answers_class = 'accepted'
            else:
                answers_class = 'some-answers'

            if question.view_count == 0:
                views_class = 'no-views'
            else:
                views_class = 'some-views'

            question_data = {
                'title': question.title,
                'summary': question.summary,
                'id': question.id,
                'tags': question.get_tag_names(),
                'votes': extra_filters.humanize_counter(question.score),
                'votes_class': votes_class,
                'votes_word': ungettext('vote', 'votes', question.score),
                'answers': extra_filters.humanize_counter(question.answer_count),
                'answers_class': answers_class,
                'answers_word': ungettext('answer', 'answers', question.answer_count),
                'views': extra_filters.humanize_counter(question.view_count),
                'views_class': views_class,
                'views_word': ungettext('view', 'views', question.view_count),
                'timestamp': unicode(timestamp),
                'timesince': functions.diff_date(timestamp),
                'u_id': author.id,
                'u_name': author.username,
                'u_rep': author.reputation,
                'u_gold': author.gold,
                'u_gold_title': pluralize_badge_count(
                                                author.gold,
                                                const.GOLD_BADGE
                                            ),
                'u_gold_badge_symbol': const.BADGE_DISPLAY_SYMBOL,
                'u_gold_css_class': gold_badge_css_class,
                'u_silver': author.silver,
                'u_silver_title': pluralize_badge_count(
                                            author.silver,
                                            const.SILVER_BADGE
                                        ),
                'u_silver_badge_symbol': const.BADGE_DISPLAY_SYMBOL,
                'u_silver_css_class': silver_badge_css_class,
                'u_bronze': author.bronze,
                'u_bronze_title': pluralize_badge_count(
                                            author.bronze,
                                            const.BRONZE_BADGE
                                        ),
                'u_bronze_badge_symbol': const.BADGE_DISPLAY_SYMBOL,
                'u_bronze_css_class': bronze_badge_css_class,
            }
            ajax_data['questions'].append(question_data)

        return HttpResponse(
                    simplejson.dumps(ajax_data),
                    mimetype = 'application/json'
                )

    tags_autocomplete = _get_tags_cache_json()

    reset_method_count = 0
    if search_state.query:
        reset_method_count += 1
    if search_state.tags:
        reset_method_count += 1
    if meta_data.get('author_name',None):
        reset_method_count += 1

    template_context = RequestContext(request, {
        'language_code': translation.get_language(),
        'reset_method_count': reset_method_count,
        'view_name': 'questions',
        'active_tab': 'questions',
        'questions' : page,
        'contributors' : contributors,
        'author_name' : meta_data.get('author_name',None),
        'tab_id' : search_state.sort,
        'questions_count' : paginator.count,
        'tags' : related_tags,
        'query': search_state.query,
        'search_tags' : search_state.tags,
        'tags_autocomplete' : tags_autocomplete,
        'is_unanswered' : False,#remove this from template
        'interesting_tag_names': meta_data.get('interesting_tag_names',None),
        'ignored_tag_names': meta_data.get('ignored_tag_names',None), 
        'sort': search_state.sort,
        'show_sort_by_relevance': askbot.conf.should_show_sort_by_relevance(),
        'scope': search_state.scope,
        'context' : paginator_context,
    })

    assert(request.is_ajax() == False)
    #ajax request is handled in a separate branch above

    #before = datetime.datetime.now()
    template = ENV.get_template('questions.html')
    response = HttpResponse(template.render(template_context))
    #after = datetime.datetime.now()
    #print after - before
    return response

def tags(request):#view showing a listing of available tags - plain list
    stag = ""
    is_paginated = True
    sortby = request.GET.get('sort', 'used')
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if request.method == "GET":
        stag = request.GET.get("query", "").strip()
        if stag != '':
            objects_list = Paginator(models.Tag.objects.filter(deleted=False).exclude(used_count=0).extra(where=['name ilike %s'], params=['%' + stag + '%']), DEFAULT_PAGE_SIZE)
        else:
            if sortby == "name":
                objects_list = Paginator(models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name"), DEFAULT_PAGE_SIZE)
            else:
                objects_list = Paginator(models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count"), DEFAULT_PAGE_SIZE)

    try:
        tags = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        tags = objects_list.page(objects_list.num_pages)

    paginator_data = {
        'is_paginated' : is_paginated,
        'pages': objects_list.num_pages,
        'page': page,
        'has_previous': tags.has_previous(),
        'has_next': tags.has_next(),
        'previous': tags.previous_page_number(),
        'next': tags.next_page_number(),
        'base_url' : reverse('tags') + '?sort=%s&amp;' % sortby
    }
    paginator_context = extra_tags.cnprog_paginator(paginator_data)
    data = {
        'view_name':'tags',
        'active_tab': 'tags',
        'page_class': 'tags-page',
        'tags' : tags,
        'stag' : stag,
        'tab_id' : sortby,
        'keywords' : stag,
        'paginator_context' : paginator_context
    }
    context = RequestContext(request, data)
    template = ENV.get_template('tags.html')
    return HttpResponse(template.render(context))

def question(request, id):#refactor - long subroutine. display question body, answers and comments
    """view that displays body of the question and 
    all answers to it
    """
    #todo: fix inheritance of sort method from questions
    default_sort_method = request.session.get('questions_sort_method', 'votes')
    form = ShowQuestionForm(request.GET, default_sort_method)
    form.full_clean()#always valid
    show_answer = form.cleaned_data['show_answer']
    show_comment = form.cleaned_data['show_comment']
    show_page = form.cleaned_data['show_page']
    is_permalink = form.cleaned_data['is_permalink']
    answer_sort_method = form.cleaned_data['answer_sort_method']

    #resolve comment and answer permalinks
    #they go first because in theory both can be moved to another question
    #this block "returns" show_post and assigns actual comment and answer
    #to show_comment and show_answer variables
    #in the case if the permalinked items or their parents are gone - redirect
    #redirect also happens if id of the object's origin post != requested id
    show_post = None #used for permalinks
    if show_comment is not None:
        #comments
        try:
            show_comment = models.Comment.objects.get(id = show_comment)
            if str(show_comment.get_origin_post().id) != id:
                return HttpResponseRedirect(show_comment.get_absolute_url())
            show_post = show_comment.content_object
            show_comment.assert_is_visible_to(request.user)
        except models.Comment.DoesNotExist:
            error_message = _(
                'Sorry, the comment you are looking for has been '
                'deleted and is no longer accessible'
            )
            request.user.message_set.create(message = error_message)
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))
        except exceptions.AnswerHidden, error:
            request.user.message_set.create(message = unicode(error))
            #use reverse function here because question is not yet loaded
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))
        except exceptions.QuestionHidden, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('index'))

    elif show_answer is not None:
        #answers
        try:
            show_post = get_object_or_404(models.Answer, id = show_answer)
            if str(show_post.question.id) != id:
                return HttpResponseRedirect(show_post.get_absolute_url())
            show_post.assert_is_visible_to(request.user)
        except django_exceptions.PermissionDenied, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))

    #load question and maybe refuse showing deleted question
    try:
        question = get_object_or_404(models.Question, id=id)
        question.assert_is_visible_to(request.user)
    except exceptions.QuestionHidden, error:
        request.user.message_set.create(message = unicode(error))
        return HttpResponseRedirect(reverse('index'))

    #redirect if slug in the url is wrong
    if request.path != question.get_absolute_url():
        logging.debug('no slug match!')
        question_url = '?'.join((
                            question.get_absolute_url(),
                            urllib.urlencode(request.GET)
                        ))
        return HttpResponseRedirect(question_url)


    logging.debug('answer_sort_method=' + unicode(answer_sort_method))
    #load answers
    answers = question.get_answers(user = request.user)
    answers = answers.select_related(depth=1)

    user_answer_votes = {}
    for answer in answers:
        vote = answer.get_user_vote(request.user)
        if vote is not None and not user_answer_votes.has_key(answer.id):
            vote_value = -1
            if vote.is_upvote():
                vote_value = 1
            user_answer_votes[answer.id] = vote_value

    view_dic = {"latest":"-added_at", "oldest":"added_at", "votes":"-score" }
    orderby = view_dic[answer_sort_method]
    if answers is not None:
        answers = answers.order_by("-accepted", orderby)

    filtered_answers = []
    for answer in answers:
        if answer.deleted == True:
            if answer.author_id == request.user.id:
                filtered_answers.append(answer)
        else:
            filtered_answers.append(answer)

    #resolve page number and comment number for permalinks
    comment_order_number = None
    if show_comment:
        show_page = show_comment.get_page_number(answers = filtered_answers)
        comment_order_number = show_comment.get_order_number()
    elif show_answer:
        show_page = show_post.get_page_number(answers = filtered_answers)

    objects_list = Paginator(filtered_answers, const.ANSWERS_PAGE_SIZE)
    if show_page > objects_list.num_pages:
        return HttpResponseRedirect(question.get_absolute_url())
    page_objects = objects_list.page(show_page)

    #count visits
    if functions.not_a_robot_request(request):
        #todo: split this out into a subroutine
        #todo: merge view counts per user and per session
        #1) view count per session
        update_view_count = False
        if 'question_view_times' not in request.session:
            request.session['question_view_times'] = {}

        last_seen = request.session['question_view_times'].get(question.id, None)
        updated_when, updated_who = question.get_last_update_info()

        if updated_who != request.user:
            if last_seen:
                if last_seen < updated_when:
                    update_view_count = True 
            else:
                update_view_count = True

        request.session['question_view_times'][question.id] = \
                                                    datetime.datetime.now()

        if update_view_count:
            question.view_count += 1
            question.save()

        #2) question view count per user and clear response displays
        if request.user.is_authenticated():
            #get response notifications
            request.user.visit_question(question)

        #3) send award badges signal for any badges
        #that are awarded for question views 
        award_badges_signal.send(None,
                        event = 'view_question',
                        actor = request.user,
                        context_object = question,
                    )

    paginator_data = {
        'is_paginated' : (objects_list.count > const.ANSWERS_PAGE_SIZE),
        'pages': objects_list.num_pages,
        'page': show_page,
        'has_previous': page_objects.has_previous(),
        'has_next': page_objects.has_next(),
        'previous': page_objects.previous_page_number(),
        'next': page_objects.next_page_number(),
        'base_url' : request.path + '?sort=%s&amp;' % answer_sort_method,
        'extend_url' : "#sort-top"
    }
    paginator_context = extra_tags.cnprog_paginator(paginator_data)

    favorited = question.has_favorite_by_user(request.user)
    if request.user.is_authenticated():
        question_vote = question.votes.select_related().filter(user=request.user)
    else:
        question_vote = None #is this correct?
    if question_vote is not None and question_vote.count() > 0:
        question_vote = question_vote[0]


    data = {
        'view_name': 'question',
        'active_tab': 'questions',
        'question' : question,
        'question_vote' : question_vote,
        'question_comment_count':question.comments.count(),
        'answer' : AnswerForm(question,request.user),
        'answers' : page_objects.object_list,
        'user_answer_votes': user_answer_votes,
        'tags' : question.tags.all(),
        'tab_id' : answer_sort_method,
        'favorited' : favorited,
        'similar_questions' : question.get_similar_questions(),
        'language_code': translation.get_language(),
        'paginator_context' : paginator_context,
        'show_post': show_post,
        'show_comment': show_comment,
        'comment_order_number': comment_order_number
    }
    if request.user.is_authenticated():
        data['tags_autocomplete'] = _get_tags_cache_json()
    context = RequestContext(request, data)
    template = ENV.get_template('question.html')
    return HttpResponse(template.render(context))

def revisions(request, id, object_name=None):
    assert(object_name in ('Question', 'Answer'))
    post = get_object_or_404(models.get_model(object_name), id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
    for i, revision in enumerate(revisions):
        revision.html = revision.as_html()
        if i == 0:
            revision.diff = revisions[i].html
            revision.summary = _('initial version')
        else:
            revision.diff = htmldiff(revisions[i-1].html, revision.html)
    data = {
        'view_name':'answer_revisions',
        'active_tab':'questions',
        'post': post,
        'revisions': revisions,
    }
    context = RequestContext(request, data)
    template = ENV.get_template('revisions.html')
    return HttpResponse(template.render(context))

@ajax_only
@anonymous_forbidden
@get_only
def get_comment(request):
    """returns text of a comment by id
    via ajax response requires request method get
    and request must be ajax
    """
    id = int(request.GET['id'])
    comment = models.Comment.objects.get(id = id)
    request.user.assert_can_edit_comment(comment)
    return {'text': comment.comment}
