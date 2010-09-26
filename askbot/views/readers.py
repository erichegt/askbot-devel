# encoding:utf-8
"""
:synopsis: views "read-only" for main textual content

By main textual content is meant - text of Questions, Answers and Comments.
The "read-only" requirement here is not 100% strict, as for example "question" view does
allow adding new comments via Ajax form post.
"""
import datetime
import logging
from urllib import unquote
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext, Context
from django.template import loader
from django.template import defaultfilters
from django.utils.html import *
from django.utils import simplejson
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils import translation
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page
from django.core import exceptions as django_exceptions
from django.contrib.humanize.templatetags import humanize

from askbot.utils.html import sanitize_html
#from lxml.html.diff import htmldiff
from askbot.utils.diff import textDiff as htmldiff
from askbot.forms import *
from askbot.models import *
from askbot import const
from askbot import auth
from askbot.utils import markup
from askbot.utils.forms import get_next_url
from askbot.utils.functions import not_a_robot_request
from askbot.utils.decorators import profile
from askbot.search.state_manager import SearchState
from askbot.templatetags import extra_tags
from askbot.templatetags import extra_filters
from askbot.conf import settings as askbot_settings
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
ANSWERS_PAGE_SIZE = 10

#system to display main content
def _get_tags_cache_json():#service routine used by views requiring tag list in the javascript space
    """returns list of all tags in json format
    no caching yet, actually
    """
    tags = Tag.objects.filter(deleted=False).all()
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

    #have this call implemented for sphinx, mysql and pgsql
    (qs, meta_data) = Question.objects.run_advanced_search(
                            request_user = request.user,
                            scope_selector = search_state.scope,#unanswered/all/favorite (for logged in)
                            search_query = search_state.query,
                            tag_selector = search_state.tags,
                            author_selector = search_state.author,
                            sort_method = search_state.sort
                        )

    objects_list = Paginator(qs, search_state.page_size)

    if objects_list.num_pages < search_state.page:
        raise Http404

    questions = objects_list.page(search_state.page)

    #todo maybe do this search on query the set instead
    related_tags = Tag.objects.get_tags_by_questions(questions.object_list)
    contributors = Question.objects.get_question_and_answer_contributors(questions.object_list)

    paginator_context = {
        'is_paginated' : True,
        'pages': objects_list.num_pages,
        'page': search_state.page,
        'has_previous': questions.has_previous(),
        'has_next': questions.has_next(),
        'previous': questions.previous_page_number(),
        'next': questions.next_page_number(),
        'base_url' : request.path + '?sort=%s&' % search_state.sort,#todo in T sort=>sort_method
        'page_size' : search_state.page_size,#todo in T pagesize -> page_size
    }

    if request.is_ajax():

        q_count = objects_list.count
        question_counter = ungettext(
                                '%(q_num)s question',
                                '%(q_num)s questions',
                                q_count
                            ) % {
                                'q_num': humanize.intcomma(q_count),
                            }

        paginator_tpl = loader.get_template('paginator.html')
        paginator_html = paginator_tpl.render(
                                    Context(
                                        extra_tags.cnprog_paginator(
                                                        paginator_context
                                                    )
                                    )
                                )
        ajax_data = {
            #current page is 1 by default now
            #because ajax is only called by update in the search button
            'paginator': paginator_html,
            'question_counter': question_counter,
            'questions': list(),
            'related_tags': list(),
            'faces': list()
        }

        badge_levels = dict(Badge.TYPE_CHOICES)
        def pluralize_badge_count(count, level):
            return ungettext(
                '%(badge_count)d %(badge_level)s badge',
                '%(badge_count)d %(badge_level)s badges',
                count
            ) % {
                'badge_count': count, 
                'badge_level': badge_levels[level]
            }

        gold_badge_css_class = Badge.CSS_CLASSES[Badge.GOLD],
        silver_badge_css_class = Badge.CSS_CLASSES[Badge.SILVER],
        bronze_badge_css_class = Badge.CSS_CLASSES[Badge.BRONZE],

        for tag in related_tags:
            tag_data = {
                'name': tag.name,
                'used_count': humanize.intcomma(tag.used_count)
            }
            ajax_data['related_tags'].append(tag_data)

        for contributor in contributors:
            ajax_data['faces'].append(extra_tags.gravatar(contributor, 48))

        votes_color_empty_fg = askbot_settings.COLORS_VOTE_COUNTER_EMPTY_FG
        votes_bgcolor_empty = askbot_settings.COLORS_VOTE_COUNTER_EMPTY_BG
        votes_color_min_fg = askbot_settings.COLORS_VOTE_COUNTER_MIN_FG
        votes_bgcolor_min = askbot_settings.COLORS_VOTE_COUNTER_MIN_BG
        answers_color_empty_fg = askbot_settings.COLORS_ANSWER_COUNTER_EMPTY_FG
        answers_bgcolor_empty = askbot_settings.COLORS_ANSWER_COUNTER_EMPTY_BG
        answers_color_accepted_fg = askbot_settings.COLORS_ANSWER_COUNTER_ACCEPTED_FG
        answers_bgcolor_accepted = askbot_settings.COLORS_ANSWER_COUNTER_ACCEPTED_BG
        answers_color_min_fg = askbot_settings.COLORS_ANSWER_COUNTER_MIN_FG
        answers_bgcolor_min = askbot_settings.COLORS_ANSWER_COUNTER_MIN_BG
        views_color_empty_fg = askbot_settings.COLORS_VIEW_COUNTER_EMPTY_FG
        views_bgcolor_empty = askbot_settings.COLORS_VIEW_COUNTER_EMPTY_BG
        views_color_min_fg = askbot_settings.COLORS_VIEW_COUNTER_MIN_FG
        views_bgcolor_min = askbot_settings.COLORS_VIEW_COUNTER_MIN_BG

        for question in questions.object_list:
            timestamp = question.last_activity_at
            author = question.last_activity_by

            if question.score == 0:
                votes_color = votes_color_empty_fg 
                votes_bgcolor = votes_bgcolor_empty
            else:
                votes_color = votes_color_min_fg 
                votes_bgcolor = votes_bgcolor_min 

            if question.answer_count == 0:
                answers_color = answers_color_empty_fg
                answers_bgcolor = answers_bgcolor_empty
            elif question.answer_accepted:
                answers_color = answers_color_accepted_fg
                answers_bgcolor = answers_bgcolor_accepted 
            else:
                answers_color = answers_color_min_fg
                answers_bgcolor = answers_bgcolor_min

            if question.view_count == 0:
                views_color = views_color_empty_fg
                views_bgcolor = views_bgcolor_empty
            else:
                views_color = views_color_min_fg
                views_bgcolor = views_bgcolor_min

            question_data = {
                'title': question.title,
                'summary': question.summary,
                'id': question.id,
                'tags': question.get_tag_names(),
                'votes': extra_filters.humanize_counter(question.score),
                'votes_color': votes_color,
                'votes_bgcolor': votes_bgcolor,
                'votes_word': ungettext('vote', 'votes', question.score),
                'answers': extra_filters.humanize_counter(question.answer_count),
                'answers_color': answers_color,
                'answers_bgcolor': answers_bgcolor,
                'answers_word': ungettext('answer', 'answers', question.answer_count),
                'views': extra_filters.humanize_counter(question.view_count),
                'views_color': views_color,
                'views_bgcolor': views_bgcolor,
                'views_word': ungettext('view', 'views', question.view_count),
                'timestamp': unicode(timestamp),
                'timesince': extra_tags.diff_date(timestamp),
                'u_id': author.id,
                'u_name': author.username,
                'u_rep': author.reputation,
                'u_gold': author.gold,
                'u_gold_title': pluralize_badge_count(
                                                author.gold,
                                                Badge.GOLD
                                            ),
                'u_gold_badge_symbol': Badge.DISPLAY_SYMBOL,
                'u_gold_css_class': gold_badge_css_class,
                'u_silver': author.silver,
                'u_silver_title': pluralize_badge_count(
                                            author.silver,
                                            Badge.SILVER
                                        ),
                'u_silver_badge_symbol': Badge.DISPLAY_SYMBOL,
                'u_silver_css_class': silver_badge_css_class,
                'u_bronze': author.bronze,
                'u_bronze_title': pluralize_badge_count(
                                            author.bronze,
                                            Badge.BRONZE
                                        ),
                'u_bronze_badge_symbol': Badge.DISPLAY_SYMBOL,
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
        'view_name': 'questions',
        'active_tab': 'questions',
        'questions' : questions,
        'contributors' : contributors,
        'author_name' : meta_data.get('author_name',None),
        'tab_id' : search_state.sort,
        'questions_count' : objects_list.count,
        'tags' : related_tags,
        'query': search_state.query,
        'search_tags' : search_state.tags,
        'tags_autocomplete' : tags_autocomplete,
        'is_unanswered' : False,#remove this from template
        'interesting_tag_names': meta_data.get('interesting_tag_names',None),
        'ignored_tag_names': meta_data.get('ignored_tag_names',None), 
        'sort': search_state.sort,
        'scope': search_state.scope,
        'context' : paginator_context,
        })

    #todo: organize variables by type
    if request.is_ajax():
        #this branch should be dead now
        raise NotImplementedError()
        template = loader.get_template('questions_ajax.html')
        question_snippet = template.render(template_context)
        output = {'question_snippet': question_snippet}
        #print simplejson.dumps(output)
        return HttpResponse(simplejson.dumps(output), mimetype='application/json')
    else:
        template = ENV.get_template('questions.jinja.html')
        return HttpResponse(template.render(template_context))
    #after = datetime.datetime.now()
    #print 'time to render %s' % (after - before)

def search(request): #generates listing of questions matching a search query - including tags and just words
    """redirects to people and tag search pages
    todo: eliminate this altogether and instead make
    search "tab" sensitive automatically - the radio-buttons
    are useless under the search bar
    """
    if request.method == "GET":
        search_type = request.GET.get('t')
        query = request.GET.get('query')
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        if search_type == 'tag':
            return HttpResponseRedirect(reverse('tags') + '?q=%s&page=%s' % (query.strip(), page))
        elif search_type == 'user':
            return HttpResponseRedirect(reverse('users') + '?q=%s&page=%s' % (query.strip(), page))
        else:
            raise Http404
    else:
        raise Http404

def tags(request):#view showing a listing of available tags - plain list
    stag = ""
    is_paginated = True
    sortby = request.GET.get('sort', 'used')
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    if request.method == "GET":
        stag = request.GET.get("q", "").strip()
        if stag != '':
            objects_list = Paginator(Tag.objects.filter(deleted=False).exclude(used_count=0).extra(where=['name like %s'], params=['%' + stag + '%']), DEFAULT_PAGE_SIZE)
        else:
            if sortby == "name":
                objects_list = Paginator(Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name"), DEFAULT_PAGE_SIZE)
            else:
                objects_list = Paginator(Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count"), DEFAULT_PAGE_SIZE)

    try:
        tags = objects_list.page(page)
    except (EmptyPage, InvalidPage):
        tags = objects_list.page(objects_list.num_pages)

    return render_to_response('tags.html', {
                                            "view_name":"tags",
                                            "active_tab": "tags",
                                            "tags" : tags,
                                            "stag" : stag,
                                            "tab_id" : sortby,
                                            "keywords" : stag,
                                            "context" : {
                                                'is_paginated' : is_paginated,
                                                'pages': objects_list.num_pages,
                                                'page': page,
                                                'has_previous': tags.has_previous(),
                                                'has_next': tags.has_next(),
                                                'previous': tags.previous_page_number(),
                                                'next': tags.next_page_number(),
                                                'base_url' : reverse('tags') + '?sort=%s&' % sortby
                                            }
                                }, context_instance=RequestContext(request))

def question(request, id):#refactor - long subroutine. display question body, answers and comments
    """view that displays body of the question and 
    all answers to it
    """
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    view_id = request.GET.get('sort', None)
    view_dic = {"latest":"-added_at", "oldest":"added_at", "votes":"-score" }
    try:
        orderby = view_dic[view_id]
    except KeyError:
        qsm = request.session.get('questions_sort_method',None)
        if qsm in ('mostvoted','latest'):
            logging.debug('loaded from session ' + qsm)
            if qsm == 'mostvoted':
                view_id = 'votes'
                orderby = '-score'
            else:
                view_id = 'latest'
                orderby = '-added_at'
        else:
            view_id = "votes"
            orderby = "-score"

    logging.debug('view_id=' + unicode(view_id))

    question = get_object_or_404(Question, id=id)
    try:
        assert(request.path == question.get_absolute_url())
    except AssertionError:
        logging.debug('no slug match!')
        return HttpResponseRedirect(question.get_absolute_url())

    if question.deleted:
        try:
            if request.user.is_anonymous():
                msg = _(
                        'Sorry, this question has been '
                        'deleted and is no longer accessible'
                    )
                raise django_exceptions.PermissionDenied(msg)
            request.user.assert_can_see_deleted_post(question)
        except django_exceptions.PermissionDenied, e:
            request.user.message_set.create(message = unicode(e))
            return HttpResponseRedirect(reverse('index'))

    answer_form = AnswerForm(question,request.user)
    answers = question.get_answers(user = request.user)
    answers = answers.select_related(depth=1)

    favorited = question.has_favorite_by_user(request.user)
    if request.user.is_authenticated():
        question_vote = question.votes.select_related().filter(user=request.user)
    else:
        question_vote = None #is this correct?
    if question_vote is not None and question_vote.count() > 0:
        question_vote = question_vote[0]

    user_answer_votes = {}
    for answer in answers:
        vote = answer.get_user_vote(request.user)
        if vote is not None and not user_answer_votes.has_key(answer.id):
            vote_value = -1
            if vote.is_upvote():
                vote_value = 1
            user_answer_votes[answer.id] = vote_value

    if answers is not None:
        answers = answers.order_by("-accepted", orderby)

    filtered_answers = []
    for answer in answers:
        if answer.deleted == True:
            if answer.author_id == request.user.id:
                filtered_answers.append(answer)
        else:
            filtered_answers.append(answer)

    objects_list = Paginator(filtered_answers, ANSWERS_PAGE_SIZE)
    page_objects = objects_list.page(page)

    if not_a_robot_request(request):
        #todo: split this out into a subroutine
        #todo: merge view counts per user and per session
        #1) view count per session
        update_view_count = False
        if 'question_view_times' not in request.session:
            request.session['question_view_times'] = {}

        last_seen = request.session['question_view_times'].get(question.id,None)
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

    return render_to_response('question.html', {
        'view_name': 'question',
        'active_tab': 'questions',
        'question' : question,
        'question_vote' : question_vote,
        'question_comment_count':question.comments.count(),
        'answer' : answer_form,
        'answers' : page_objects.object_list,
        'user_answer_votes': user_answer_votes,
        'tags' : question.tags.all(),
        'tab_id' : view_id,
        'favorited' : favorited,
        'similar_questions' : question.get_similar_questions(),
        'context' : {
            'is_paginated' : True,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': page_objects.has_previous(),
            'has_next': page_objects.has_next(),
            'previous': page_objects.previous_page_number(),
            'next': page_objects.next_page_number(),
            'base_url' : request.path + '?sort=%s&' % view_id,
            'extend_url' : "#sort-top"
        }
        }, context_instance=RequestContext(request))

QUESTION_REVISION_TEMPLATE = ('<h1>%(title)s</h1>\n'
                              '<div class="text">%(html)s</div>\n'
                              '<div class="tags">%(tags)s</div>')
def question_revisions(request, id):
    post = get_object_or_404(Question, id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
    markdowner = markup.get_parser()
    for i, revision in enumerate(revisions):
        revision.html = QUESTION_REVISION_TEMPLATE % {
            'title': revision.title,
            'html': sanitize_html(markdowner.convert(revision.text)),
            'tags': ' '.join(['<a class="post-tag">%s</a>' % tag
                              for tag in revision.tagnames.split(' ')]),
        }
        if i > 0:
            revisions[i].diff = htmldiff(revisions[i-1].html, revision.html)
        else:
            revisions[i].diff = QUESTION_REVISION_TEMPLATE % {
                'title': revisions[0].title,
                'html': sanitize_html(markdowner.convert(revisions[0].text)),
                'tags': ' '.join(['<a class="post-tag">%s</a>' % tag
                                 for tag in revisions[0].tagnames.split(' ')]),
            }
            revisions[i].summary = _('initial version') 
    return render_to_response('revisions_question.html', {
                              'view_name':'question_revisions',
                              'active_tab':'questions',
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

ANSWER_REVISION_TEMPLATE = ('<div class="text">%(html)s</div>')
def answer_revisions(request, id):
    post = get_object_or_404(Answer, id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
    markdowner = markup.get_parser()
    for i, revision in enumerate(revisions):
        revision.html = ANSWER_REVISION_TEMPLATE % {
            'html': sanitize_html(markdowner.convert(revision.text))
        }
        if i > 0:
            revisions[i].diff = htmldiff(revisions[i-1].html, revision.html)
        else:
            revisions[i].diff = revisions[i].text
            revisions[i].summary = _('initial version')
    return render_to_response('revisions_answer.html', {
                              'view_name':'answer_revisions',
                              'active_tab':'questions',
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

