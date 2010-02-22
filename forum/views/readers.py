# encoding:utf-8
import datetime
import logging
from urllib import unquote
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext
from django.utils.html import *
from django.utils import simplejson
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict

from forum.utils.html import sanitize_html
from markdown2 import Markdown
#from lxml.html.diff import htmldiff
from forum.utils.diff import textDiff as htmldiff
from forum.forms import *
from forum.models import *
from forum.auth import *
from forum.const import *
from forum import auth
from forum.utils.forms import get_next_url

# used in index page
#refactor - move these numbers somewhere?
INDEX_PAGE_SIZE = 30
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 25
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in questions
QUESTIONS_PAGE_SIZE = 30
# used in answers
ANSWERS_PAGE_SIZE = 10

markdowner = Markdown(html4tags=True)

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

def _get_and_remember_questions_sort_method(request, view_dic, default):#service routine used by q listing views and question view
    """manages persistence of post sort order
    it is assumed that when user wants newest question - 
    then he/she wants newest answers as well, etc.
    how far should this assumption actually go - may be a good question
    """
    if default not in view_dic:
        raise Exception('default value must be in view_dic')

    q_sort_method = request.REQUEST.get('sort', None)
    if q_sort_method == None:
        q_sort_method = request.session.get('questions_sort_method', default)

    if q_sort_method not in view_dic:
        q_sort_method = default
    request.session['questions_sort_method'] = q_sort_method
    return q_sort_method, view_dic[q_sort_method]

#refactor? - we have these
#views that generate a listing of questions in one way or another:
#index, unanswered, questions, search, tag
#should we dry them up?
#related topics - information drill-down, search refinement

def index(request):#generates front page - shows listing of questions sorted in various ways
    """index view mapped to the root url of the Q&A site
    """
    view_dic = {
             "latest":"-last_activity_at",
             "hottest":"-answer_count",
             "mostvoted":"-score",
             }
    view_id, orderby = _get_and_remember_questions_sort_method(request, view_dic, 'latest')

    pagesize = request.session.get("pagesize",QUESTIONS_PAGE_SIZE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    qs = Question.objects.exclude(deleted=True).order_by(orderby)

    objects_list = Paginator(qs, pagesize)
    questions = objects_list.page(page)

    # RISK - inner join queries
    #questions = questions.select_related()
    tags = Tag.objects.get_valid_tags(INDEX_TAGS_SIZE)

    awards = Award.objects.get_recent_awards()

    (interesting_tag_names, ignored_tag_names) = (None, None)
    if request.user.is_authenticated():
        pt = MarkedTag.objects.filter(user=request.user)
        interesting_tag_names = pt.filter(reason='good').values_list('tag__name', flat=True)
        ignored_tag_names = pt.filter(reason='bad').values_list('tag__name', flat=True)

    tags_autocomplete = _get_tags_cache_json()

    return render_to_response('index.html', {
        'interesting_tag_names': interesting_tag_names,
        'tags_autocomplete': tags_autocomplete,
        'ignored_tag_names': ignored_tag_names,
        "questions" : questions,
        "tab_id" : view_id,
        "tags" : tags,
        "awards" : awards[:INDEX_AWARD_SIZE],
        "context" : {
            'is_paginated' : True,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': questions.has_previous(),
            'has_next': questions.has_next(),
            'previous': questions.previous_page_number(),
            'next': questions.next_page_number(),
            'base_url' : request.path + '?sort=%s&' % view_id,
            'pagesize' : pagesize
        }}, context_instance=RequestContext(request))

def unanswered(request):#generates listing of unanswered questions
    return questions(request, unanswered=True)

def questions(request, tagname=None, unanswered=False):#a view generating listing of questions, used by 'unanswered' too
    """
    List of Questions, Tagged questions, and Unanswered questions.
    """
    # template file
    # "questions.html" or maybe index.html in the future
    template_file = "questions.html"
    # Set flag to False by default. If it is equal to True, then need to be saved.
    pagesize_changed = False
    # get pagesize from session, if failed then get default value
    pagesize = request.session.get("pagesize",QUESTIONS_PAGE_SIZE)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    view_dic = {"latest":"-added_at", "active":"-last_activity_at", "hottest":"-answer_count", "mostvoted":"-score" }
    view_id, orderby = _get_and_remember_questions_sort_method(request,view_dic,'latest')

    # check if request is from tagged questions
    qs = Question.objects.exclude(deleted=True)

    if tagname is not None:
        qs = qs.filter(tags__name = unquote(tagname))

    if unanswered:
        qs = qs.exclude(answer_accepted=True)

    author_name = None
    #user contributed questions & answers
    if 'user' in request.GET:
        try:
            author_name = request.GET['user']
            u = User.objects.get(username=author_name)
            qs = qs.filter(Q(author=u) | Q(answers__author=u))
        except User.DoesNotExist:
            author_name = None

    if request.user.is_authenticated():
        uid_str = str(request.user.id)
        qs = qs.extra(
                        select = SortedDict([
                            (
                                'interesting_score', 
                                'SELECT COUNT(1) FROM forum_markedtag, question_tags '
                                  + 'WHERE forum_markedtag.user_id = %s '
                                  + 'AND forum_markedtag.tag_id = question_tags.tag_id '
                                  + 'AND forum_markedtag.reason = \'good\' '
                                  + 'AND question_tags.question_id = question.id'
                            ),
                                ]),
                        select_params = (uid_str,),
                     )
        if request.user.hide_ignored_questions:
            ignored_tags = Tag.objects.filter(user_selections__reason='bad',
                                            user_selections__user = request.user)
            qs = qs.exclude(tags__in=ignored_tags)
        else:
            qs = qs.extra(
                        select = SortedDict([
                            (
                                'ignored_score', 
                                'SELECT COUNT(1) FROM forum_markedtag, question_tags '
                                  + 'WHERE forum_markedtag.user_id = %s '
                                  + 'AND forum_markedtag.tag_id = question_tags.tag_id '
                                  + 'AND forum_markedtag.reason = \'bad\' '
                                  + 'AND question_tags.question_id = question.id'
                            )
                                ]),
                        select_params = (uid_str, )
                     )

    qs = qs.select_related(depth=1).order_by(orderby)

    objects_list = Paginator(qs, pagesize)
    questions = objects_list.page(page)

    # Get related tags from this page objects
    if questions.object_list.count() > 0:
        related_tags = Tag.objects.get_tags_by_questions(questions.object_list)
    else:
        related_tags = None
    tags_autocomplete = _get_tags_cache_json()

    # get the list of interesting and ignored tags
    (interesting_tag_names, ignored_tag_names) = (None, None)
    if request.user.is_authenticated():
        pt = MarkedTag.objects.filter(user=request.user)
        interesting_tag_names = pt.filter(reason='good').values_list('tag__name', flat=True)
        ignored_tag_names = pt.filter(reason='bad').values_list('tag__name', flat=True)

    return render_to_response(template_file, {
        "questions" : questions,
        "author_name" : author_name,
        "tab_id" : view_id,
        "questions_count" : objects_list.count,
        "tags" : related_tags,
        "tags_autocomplete" : tags_autocomplete, 
        "searchtag" : tagname,
        "is_unanswered" : unanswered,
        "interesting_tag_names": interesting_tag_names,
        'ignored_tag_names': ignored_tag_names, 
        "context" : {
            'is_paginated' : True,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': questions.has_previous(),
            'has_next': questions.has_next(),
            'previous': questions.previous_page_number(),
            'next': questions.next_page_number(),
            'base_url' : request.path + '?sort=%s&' % view_id,
            'pagesize' : pagesize
        }}, context_instance=RequestContext(request))

def search(request): #generates listing of questions matching a search query - including tags and just words
    """generates listing of questions matching a search query
    supports full text search in mysql db using sphinx and internally in postgresql
    falls back on simple partial string matching approach if
    full text search function is not available
    """
    if request.method == "GET":
        keywords = request.GET.get("q")
        search_type = request.GET.get("t")
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        if keywords is None:
            return HttpResponseRedirect(reverse(index))
        if search_type == 'tag':
            return HttpResponseRedirect(reverse('tags') + '?q=%s&page=%s' % (keywords.strip(), page))
        elif search_type == "user":
            return HttpResponseRedirect(reverse('users') + '?q=%s&page=%s' % (keywords.strip(), page))
        elif search_type == "question":
            
            template_file = "questions.html"
            # Set flag to False by default. If it is equal to True, then need to be saved.
            pagesize_changed = False
            # get pagesize from session, if failed then get default value
            user_page_size = request.session.get("pagesize", QUESTIONS_PAGE_SIZE)
            # set pagesize equal to logon user specified value in database
            if request.user.is_authenticated() and request.user.questions_per_page > 0:
                user_page_size = request.user.questions_per_page

            try:
                page = int(request.GET.get('page', '1'))
                # get new pagesize from UI selection
                pagesize = int(request.GET.get('pagesize', user_page_size))
                if pagesize <> user_page_size:
                    pagesize_changed = True

            except ValueError:
                page = 1
                pagesize  = user_page_size

            # save this pagesize to user database
            if pagesize_changed:
                request.session["pagesize"] = pagesize
                if request.user.is_authenticated():
                    user = request.user
                    user.questions_per_page = pagesize
                    user.save()

            view_id = request.GET.get('sort', None)
            view_dic = {"latest":"-added_at", "active":"-last_activity_at", "hottest":"-answer_count", "mostvoted":"-score" }
            try:
                orderby = view_dic[view_id]
            except KeyError:
                view_id = "latest"
                orderby = "-added_at"

            def question_search(keywords, orderby):
                objects = Question.objects.filter(deleted=False).extra(where=['title like %s'], params=['%' + keywords + '%']).order_by(orderby)
                # RISK - inner join queries
                return objects.select_related();

            from forum.modules import get_handler

            question_search = get_handler('question_search', question_search)
            
            objects = question_search(keywords, orderby)

            objects_list = Paginator(objects, pagesize)
            questions = objects_list.page(page)

            # Get related tags from this page objects
            related_tags = []
            for question in questions.object_list:
                tags = list(question.tags.all())
                for tag in tags:
                    if tag not in related_tags:
                        related_tags.append(tag)

            #if is_search is true in the context, prepend this string to soting tabs urls
            search_uri = "?q=%s&page=%d&t=question" % ("+".join(keywords.split()),  page)

            return render_to_response(template_file, {
                "questions" : questions,
                "tab_id" : view_id,
                "questions_count" : objects_list.count,
                "tags" : related_tags,
                "searchtag" : None,
                "searchtitle" : keywords,
                "keywords" : keywords,
                "is_unanswered" : False,
                "is_search": True, 
                "search_uri":  search_uri, 
                "context" : {
                    'is_paginated' : True,
                    'pages': objects_list.num_pages,
                    'page': page,
                    'has_previous': questions.has_previous(),
                    'has_next': questions.has_next(),
                    'previous': questions.previous_page_number(),
                    'next': questions.next_page_number(),
                    'base_url' : request.path + '?t=question&q=%s&sort=%s&' % (keywords, view_id),
                    'pagesize' : pagesize
                }}, context_instance=RequestContext(request))
 
    else:
        raise Http404

def tag(request, tag):#stub generates listing of questions tagged with a single tag
    return questions(request, tagname=tag)

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

    logging.debug('view_id=' + str(view_id))

    question = get_object_or_404(Question, id=id)
    try:
        pattern = r'/%s%s%d/([\w-]+)' % (settings.FORUM_SCRIPT_ALIAS,_('question/'), question.id)
        path_re = re.compile(pattern)
        logging.debug(pattern)
        logging.debug(request.path)
        m = path_re.match(request.path)
        if m:
            slug = m.group(1)
            logging.debug('have slug %s' % slug)
            assert(slug == slugify(question.title))
        else:
            logging.debug('no match!')
    except:
        return HttpResponseRedirect(question.get_absolute_url())

    if question.deleted and not auth.can_view_deleted_post(request.user, question):
        raise Http404
    answer_form = AnswerForm(question,request.user)
    answers = Answer.objects.get_answers_from_question(question, request.user)
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

    request.session['question_view_times'][question.id] = datetime.datetime.now()

    if update_view_count:
        question.view_count += 1
        question.save()

    #2) question view count per user
    if request.user.is_authenticated():
        try:
            question_view = QuestionView.objects.get(who=request.user, question=question)
        except QuestionView.DoesNotExist:
            question_view = QuestionView(who=request.user, question=question)
        question_view.when = datetime.datetime.now()
        question_view.save()

    return render_to_response('question.html', {
        "question" : question,
        "question_vote" : question_vote,
        "question_comment_count":question.comments.count(),
        "answer" : answer_form,
        "answers" : page_objects.object_list,
        "user_answer_votes": user_answer_votes,
        "tags" : question.tags.all(),
        "tab_id" : view_id,
        "favorited" : favorited,
        "similar_questions" : Question.objects.get_similar_questions(question),
        "context" : {
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
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

ANSWER_REVISION_TEMPLATE = ('<div class="text">%(html)s</div>')
def answer_revisions(request, id):
    post = get_object_or_404(Answer, id=id)
    revisions = list(post.revisions.all())
    revisions.reverse()
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
                              'post': post,
                              'revisions': revisions,
                              }, context_instance=RequestContext(request))

