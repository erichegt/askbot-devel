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
import operator
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import Context
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils import translation
from django.views.decorators import csrf
from django.core.urlresolvers import reverse
from django.core import exceptions as django_exceptions
from django.contrib.humanize.templatetags import humanize
from django.http import QueryDict

import askbot
from askbot import exceptions
from askbot.utils.diff import textDiff as htmldiff
from askbot.forms import AdvancedSearchForm, AnswerForm, ShowQuestionForm
from askbot import models
from askbot import schedules
from askbot.models.badges import award_badges_signal
from askbot import const
from askbot.utils import functions
from askbot.utils.decorators import anonymous_forbidden, ajax_only, get_only
from askbot.search.state_manager import SearchState
from askbot.templatetags import extra_tags
import askbot.conf
from askbot.conf import settings as askbot_settings
from askbot.skins.loaders import render_into_skin, get_template#jinja2 template loading enviroment

# used in index page
#todo: - take these out of const or settings
from askbot.models import Post, Vote

INDEX_PAGE_SIZE = 30
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 25
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in questions
# used in answers

#refactor? - we have these
#views that generate a listing of questions in one way or another:
#index, unanswered, questions, search, tag
#should we dry them up?
#related topics - information drill-down, search refinement

def index(request):#generates front page - shows listing of questions sorted in various ways
    """index view mapped to the root url of the Q&A site
    """
    return HttpResponseRedirect(reverse('questions'))

def questions(request, scope=const.DEFAULT_POST_SCOPE, sort=const.DEFAULT_POST_SORT_METHOD, query=None, \
        search=None, tags=None, author=None, page=None, reset_tags=None, \
        reset_author=None, reset_query=None, start_over=True, \
        remove_tag=None, page_size=None):
    """
    List of Questions, Tagged questions, and Unanswered questions.
    matching search query or user selection
    """
    if request.method == 'POST':    # TODO: This is 405 condition, not 404. Django 1.2+ has decorator for this: https://docs.djangoproject.com/en/1.2/topics/http/decorators/#django.views.decorators.http.require_GET
        raise Http404

    #make parameters dictionary
    params_dict = {
        'scope': scope,
        'sort': sort,
    }
    for arg_name in ('query', 'tags'):
        if locals().get(arg_name, None):
            params_dict[arg_name] = ' '.join(locals()[arg_name].split('+'))
    for arg_name in ('search', 'author', 'page', 'reset_tags', 'reset_author', 'reset_query', 'start_over', 'remove_tag', 'page_size'):
        if locals().get(arg_name, None):
            params_dict[arg_name] = locals()[arg_name]
    
    #update search state
    form = AdvancedSearchForm(params_dict)
    if form.is_valid():
        user_input = form.cleaned_data
    else:
        user_input = None
    search_state = request.session.get('search_state', SearchState())
    view_log = request.session['view_log']
    search_state.update(user_input, view_log, request.user)
    request.session['search_state'] = search_state
    request.session.modified = True

    qs, meta_data, related_tags = models.Thread.objects.run_advanced_search(request_user=request.user, search_state=search_state)

    tag_list_type = askbot_settings.TAG_LIST_FORMAT
    if tag_list_type == 'cloud': #force cloud to sort by name
        related_tags = sorted(related_tags, key = operator.attrgetter('name'))

    paginator = Paginator(qs, search_state.page_size)
    if paginator.num_pages < search_state.page:
        search_state.page = 1
    page = paginator.page(search_state.page)

    contributors_threads = models.Thread.objects.filter(id__in=[post.thread_id for post in page.object_list])
    contributors = models.Thread.objects.get_thread_contributors(contributors_threads)

    paginator_context = {
        'is_paginated' : (paginator.count > search_state.page_size),
        'pages': paginator.num_pages,
        'page': search_state.page,
        'has_previous': page.has_previous(),
        'has_next': page.has_next(),
        'previous': page.previous_page_number(),
        'next': page.next_page_number(),
        'base_url' : search_state.query_string(),#todo in T sort=>sort_method
        'page_size' : search_state.page_size,#todo in T pagesize -> page_size
        'parameters': search_state.make_parameters(),
    }

    # We need to pass the rss feed url based
    # on the search state to the template.
    # We use QueryDict to get a querystring
    # from dicts and arrays. Much cleaner
    # than parsing and string formating.
    rss_query_dict = QueryDict("").copy()
    if search_state.query:
        # We have search string in session - pass it to
        # the QueryDict
        rss_query_dict.update({"q": search_state.query})
    if search_state.tags:
        # We have tags in session - pass it to the
        # QueryDict but as a list - we want tags+
        rss_query_dict.setlist("tags", search_state.tags)
    context_feed_url = '/feeds/rss/?%s' % rss_query_dict.urlencode() # Format the url with the QueryDict

    reset_method_count = len(filter(None, [search_state.query, search_state.tags, meta_data.get('author_name', None)]))

    if request.is_ajax():

        q_count = paginator.count
        if search_state.tags:
            question_counter = ungettext(
                                    '%(q_num)s question, tagged',
                                    '%(q_num)s questions, tagged',
                                    q_count
                                ) % {
                                    'q_num': humanize.intcomma(q_count),
                                }
        else:
            question_counter = ungettext(
                                    '%(q_num)s question',
                                    '%(q_num)s questions',
                                    q_count
                                ) % {
                                    'q_num': humanize.intcomma(q_count),
                                }

        if q_count > search_state.page_size:
            paginator_tpl = get_template('main_page/paginator.html', request)
            #todo: remove this patch on context after all templates are moved to jinja
            #paginator_context['base_url'] = request.path + '?sort=%s&' % search_state.sort
            data = {
                'context': extra_tags.cnprog_paginator(paginator_context),
                'questions_count': q_count,
                'page_size' : search_state.page_size,
            }
            paginator_html = paginator_tpl.render(Context(data))
        else:
            paginator_html = ''
        search_tags = list()
        if search_state.tags:
            search_tags = list(search_state.tags)
        query_data = {
            'tags': search_tags,
            'sort_order': search_state.sort
        }
        ajax_data = {
            #current page is 1 by default now
            #because ajax is only called by update in the search button
            'query_data': query_data,
            'paginator': paginator_html,
            'question_counter': question_counter,
            'questions': list(),
            'related_tags': list(),
            'faces': [extra_tags.gravatar(contributor, 48) for contributor in contributors],
            'feed_url': context_feed_url,
            'query_string': search_state.query_string(),
            'parameters': search_state.make_parameters(),
            'page_size' : search_state.page_size,
        }

        for tag in related_tags:
            tag_data = {
                'name': tag.name,
                'used_count': humanize.intcomma(tag.local_used_count)
            }
            ajax_data['related_tags'].append(tag_data)

        #we render the template
        #from django.template import RequestContext
        questions_tpl = get_template('main_page/questions_loop.html', request)
        #todo: remove this patch on context after all templates are moved to jinja
        data = {
            'questions': page,
            'questions_count': q_count,
            'context': paginator_context,
            'language_code': translation.get_language(),
            'query': search_state.query,
            'reset_method_count': reset_method_count,
            'query_string': search_state.query_string(),
        }

        questions_html = questions_tpl.render(Context(data))
        #import pdb; pdb.set_trace()
        ajax_data['questions'] = questions_html.replace('\n','')
        return HttpResponse(
                    simplejson.dumps(ajax_data),
                    mimetype = 'application/json'
                )

    else: # non-AJAX branch

        template_data = {
            'active_tab': 'questions',
            'author_name' : meta_data.get('author_name',None),
            'contributors' : contributors,
            'context' : paginator_context,
            'is_unanswered' : False,#remove this from template
            'interesting_tag_names': meta_data.get('interesting_tag_names',None),
            'ignored_tag_names': meta_data.get('ignored_tag_names',None),
            'language_code': translation.get_language(),
            'name_of_anonymous_user' : models.get_name_of_anonymous_user(),
            'page_class': 'main-page',
            'page_size': search_state.page_size,
            'query': search_state.query,
            'questions' : page,
            'questions_count' : paginator.count,
            'reset_method_count': reset_method_count,
            'scope': search_state.scope,
            'show_sort_by_relevance': askbot.conf.should_show_sort_by_relevance(),
            'search_tags' : search_state.tags,
            'sort': search_state.sort,
            'tab_id' : search_state.sort,
            'tags' : related_tags,
            'tag_list_type' : tag_list_type,
            'font_size' : extra_tags.get_tag_font_size(related_tags),
            'tag_filter_strategy_choices': const.TAG_FILTER_STRATEGY_CHOICES,
            'update_avatar_data': schedules.should_update_avatar_data(request),
            'query_string': search_state.query_string(),
            'parameters': search_state.make_parameters(),
            'feed_url': context_feed_url,
        }

        return render_into_skin('main_page.html', template_data, request)

def tags(request):#view showing a listing of available tags - plain list

    tag_list_type = askbot_settings.TAG_LIST_FORMAT

    if tag_list_type == 'list':

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
                objects_list = Paginator(
                                models.Tag.objects.filter(
                                                    deleted=False,
                                                    name__icontains=stag
                                                ).exclude(
                                                    used_count=0
                                                ),
                                DEFAULT_PAGE_SIZE
                            )
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
            'active_tab': 'tags',
            'page_class': 'tags-page',
            'tags' : tags,
            'tag_list_type' : tag_list_type,
            'stag' : stag,
            'tab_id' : sortby,
            'keywords' : stag,
            'paginator_context' : paginator_context
        }

    else:

        stag = ""
        sortby = request.GET.get('sort', 'name')

        if request.method == "GET":
            stag = request.GET.get("query", "").strip()
            if stag != '':
                tags = models.Tag.objects.filter(deleted=False, name__icontains=stag).exclude(used_count=0)
            else:
                if sortby == "name":
                    tags = models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name")
                else:
                    tags = models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count")

        font_size = extra_tags.get_tag_font_size(tags)

        data = {
            'active_tab': 'tags',
            'page_class': 'tags-page',
            'tags' : tags,
            'tag_list_type' : tag_list_type,
            'font_size' : font_size,
            'stag' : stag,
            'tab_id' : sortby,
            'keywords' : stag,
        }

    return render_into_skin('tags.html', data, request)

@csrf.csrf_protect
#@cache_page(60 * 5)
def question(request, id):#refactor - long subroutine. display question body, answers and comments
    """view that displays body of the question and
    all answers to it
    """
    #process url parameters
    #todo: fix inheritance of sort method from questions
    default_sort_method = request.session.get('questions_sort_method', 'votes')
    form = ShowQuestionForm(request.GET, default_sort_method)
    form.full_clean()#always valid
    show_answer = form.cleaned_data['show_answer']
    show_comment = form.cleaned_data['show_comment']
    show_page = form.cleaned_data['show_page']
    answer_sort_method = form.cleaned_data['answer_sort_method']

    # Handle URL mapping - from old Q/A/C/ URLs to the new one
    if not models.Post.objects.get_questions().filter(id=id).exists() and models.Post.objects.get_questions().filter(old_question_id=id).exists():
        old_question = models.Post.objects.get_questions().get(old_question_id=id)

        # If we are supposed to show a specific answer or comment, then just redirect to the new URL...
        if show_answer:
            try:
                old_answer = models.Post.objects.get_answers().get(old_answer_id=show_answer)
                return HttpResponseRedirect(old_answer.get_absolute_url())
            except models.Post.DoesNotExist:
                pass

        elif show_comment:
            try:
                old_comment = models.Post.objects.get_comments().get(old_comment_id=show_comment)
                return HttpResponseRedirect(old_comment.get_absolute_url())
            except models.Post.DoesNotExist:
                pass

        # ...otherwise just patch question.id, to make URLs like this one work: /question/123#345
        # This is because URL fragment (hash) (i.e. #345) is not passed to the server so we can't know which
        # answer user expects to see. If we made a redirect to the new question.id then that hash would be lost.
        # And if we just hack the question.id (and in question.html template /or its subtemplate/ we create anchors for both old and new id-s)
        # then everything should work as expected.
        id = old_question.id


    #resolve comment and answer permalinks
    #they go first because in theory both can be moved to another question
    #this block "returns" show_post and assigns actual comment and answer
    #to show_comment and show_answer variables
    #in the case if the permalinked items or their parents are gone - redirect
    #redirect also happens if id of the object's origin post != requested id
    show_post = None #used for permalinks
    if show_comment:
        #if url calls for display of a specific comment,
        #check that comment exists, that it belongs to
        #the current question
        #if it is an answer comment and the answer is hidden -
        #redirect to the default view of the question
        #if the question is hidden - redirect to the main page
        #in addition - if url points to a comment and the comment
        #is for the answer - we need the answer object
        try:
            show_comment = models.Post.objects.get_comments().get(id=show_comment)
        except models.Post.DoesNotExist:
            error_message = _(
                'Sorry, the comment you are looking for has been '
                'deleted and is no longer accessible'
            )
            request.user.message_set.create(message = error_message)
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))

        if str(show_comment.thread._question_post().id) != str(id):
            return HttpResponseRedirect(show_comment.get_absolute_url())
        show_post = show_comment.parent

        try:
            show_comment.assert_is_visible_to(request.user)
        except exceptions.AnswerHidden, error:
            request.user.message_set.create(message = unicode(error))
            #use reverse function here because question is not yet loaded
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))
        except exceptions.QuestionHidden, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('index'))

    elif show_answer:
        #if the url calls to view a particular answer to 
        #question - we must check whether the question exists
        #whether answer is actually corresponding to the current question
        #and that the visitor is allowed to see it
        show_post = get_object_or_404(models.Post, post_type='answer', id=show_answer)
        if str(show_post.thread._question_post().id) != str(id):
            return HttpResponseRedirect(show_post.get_absolute_url())

        try:
            show_post.assert_is_visible_to(request.user)
        except django_exceptions.PermissionDenied, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('question', kwargs = {'id': id}))

    #load question and maybe refuse showing deleted question
    try:
        question_post = get_object_or_404(models.Post, post_type='question', id=id)
        question_post.assert_is_visible_to(request.user)
    except exceptions.QuestionHidden, error:
        request.user.message_set.create(message = unicode(error))
        return HttpResponseRedirect(reverse('index'))

    thread = question_post.thread

    #redirect if slug in the url is wrong
    if request.path.split('/')[-1] != question_post.slug:
        logging.debug('no slug match!')
        question_url = '?'.join((
                            question_post.get_absolute_url(),
                            urllib.urlencode(request.GET)
                        ))
        return HttpResponseRedirect(question_url)

    logging.debug('answer_sort_method=' + unicode(answer_sort_method))

    #load answers
    answers = thread.get_answers(user = request.user)
    answers = answers.select_related('thread', 'author', 'last_edited_by')
    answers = answers.order_by({"latest":"-added_at", "oldest":"added_at", "votes":"-score" }[answer_sort_method])
    answers = list(answers)

    Post.objects.precache_comments(for_posts=[question_post] + answers, visitor=request.user)

    if thread.accepted_answer: # Put the accepted answer to front
        answers.remove(thread.accepted_answer)
        answers.insert(0, thread.accepted_answer)

    user_answer_votes = {}
    if request.user.is_authenticated():
        votes = Vote.objects.filter(user=request.user, voted_post__in=answers)
        for vote in votes:
            user_answer_votes[vote.voted_post.id] = int(vote)

    filtered_answers = [answer for answer in answers if ((not answer.deleted) or (answer.deleted and answer.author_id == request.user.id))]

    #resolve page number and comment number for permalinks
    show_comment_position = None
    if show_comment:
        show_page = show_comment.get_page_number(answer_posts=filtered_answers)
        show_comment_position = show_comment.get_order_number()
    elif show_answer:
        show_page = show_post.get_page_number(answer_posts=filtered_answers)

    objects_list = Paginator(filtered_answers, const.ANSWERS_PAGE_SIZE)
    if show_page > objects_list.num_pages:
        return HttpResponseRedirect(question_post.get_absolute_url())
    page_objects = objects_list.page(show_page)

    #count visits
    if functions.not_a_robot_request(request):
        #todo: split this out into a subroutine
        #todo: merge view counts per user and per session
        #1) view count per session
        update_view_count = False
        if 'question_view_times' not in request.session:
            request.session['question_view_times'] = {}

        last_seen = request.session['question_view_times'].get(question_post.id, None)

        updated_when, updated_who = thread.get_last_update_info()

        if updated_who != request.user:
            if last_seen:
                if last_seen < updated_when:
                    update_view_count = True
            else:
                update_view_count = True

        request.session['question_view_times'][question_post.id] = \
                                                    datetime.datetime.now()

        if update_view_count:
            thread.increase_view_count()

        #2) question view count per user and clear response displays
        if request.user.is_authenticated():
            #get response notifications
            request.user.visit_question(question_post)

        #3) send award badges signal for any badges
        #that are awarded for question views
        award_badges_signal.send(None,
                        event = 'view_question',
                        actor = request.user,
                        context_object = question_post,
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

    favorited = thread.has_favorite_by_user(request.user)
    user_question_vote = 0
    if request.user.is_authenticated():
        votes = question_post.votes.select_related().filter(user=request.user)
        try:
            user_question_vote = int(votes[0])
        except IndexError:
            user_question_vote = 0

    data = {
        'page_class': 'question-page',
        'active_tab': 'questions',
        'question' : question_post,
        'thread': thread,
        'user_question_vote' : user_question_vote,
        'question_comment_count': question_post.comments.count(),
        'answer' : AnswerForm(question_post, request.user),
        'answers' : page_objects.object_list,
        'user_answer_votes': user_answer_votes,
        'tags' : thread.tags.all(),
        'tab_id' : answer_sort_method,
        'favorited' : favorited,
        'similar_threads' : thread.get_similar_threads(),
        'language_code': translation.get_language(),
        'paginator_context' : paginator_context,
        'show_post': show_post,
        'show_comment': show_comment,
        'show_comment_position': show_comment_position
    }

    return render_into_skin('question.html', data, request)

def revisions(request, id, object_name=None):
    if object_name == 'Question':
        post = get_object_or_404(models.Post, post_type='question', id=id)
    else:
        post = get_object_or_404(models.Post, post_type='answer', id=id)
    revisions = list(models.PostRevision.objects.filter(post=post))
    revisions.reverse()
    for i, revision in enumerate(revisions):
        revision.html = revision.as_html()
        if i == 0:
            revision.diff = revisions[i].html
            revision.summary = _('initial version')
        else:
            revision.diff = htmldiff(revisions[i-1].html, revision.html)

    data = {
        'page_class':'revisions-page',
        'active_tab':'questions',
        'post': post,
        'revisions': revisions,
    }
    return render_into_skin('revisions.html', data, request)

@csrf.csrf_exempt
@ajax_only
@anonymous_forbidden
@get_only
def get_comment(request):
    """returns text of a comment by id
    via ajax response requires request method get
    and request must be ajax
    """
    id = int(request.GET['id'])
    comment = models.Post.objects.get(post_type='comment', id=id)
    request.user.assert_can_edit_comment(comment)
    return {'text': comment.text}

@csrf.csrf_exempt
@ajax_only
@get_only
def get_question_body(request):
    search_state = request.session.get('search_state', SearchState())
    view_log = request.session['view_log']
    (qs, meta_data, related_tags) = models.Thread.objects.run_advanced_search(
                                            request_user = request.user,
                                            search_state = search_state)
    paginator = Paginator(qs, search_state.page_size)
    page = paginator.page(search_state.page)
    questions_dict = {}
    for question in page.object_list:
        questions_dict['question-%s' % question.id] = question.summary

    return {'questions-titles': questions_dict}

def widget_questions(request):
    """Returns the first x questions based on certain tags.
    @returns template with those questions listed."""
    # make sure this is a GET request with the correct parameters.
    if request.method != 'GET':
        raise Http404
    threads = models.Thread.objects.all()
    tags_input = request.GET.get('tags','').strip()
    if len(tags_input) > 0:
        tags = [tag.strip() for tag in tags_input.split(',')]
        threads = threads.filter(tags__name__in=tags)
    data = {
        'threads': threads[:askbot_settings.QUESTIONS_WIDGET_MAX_QUESTIONS]
    }
    return render_into_skin('question_widget.html', data, request) 
    
