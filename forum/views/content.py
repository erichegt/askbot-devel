# encoding:utf-8
import os.path
import time, datetime, calendar, random
import logging
from urllib import quote, unquote
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import RequestContext, loader
from django.utils.html import *
from django.utils import simplejson
from django.core import serializers
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import slugify
from django.core.exceptions import PermissionDenied

from utils.html import sanitize_html
from utils.decorators import ajax_method, ajax_login_required
from markdown2 import Markdown
#from lxml.html.diff import htmldiff
from forum.diff import textDiff as htmldiff
from forum.forms import *
from forum.models import *
from forum.auth import *
from forum.const import *
from forum import auth
from utils.forms import get_next_url

# used in index page
INDEX_PAGE_SIZE = 20
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 100
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in questions
QUESTIONS_PAGE_SIZE = 10
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

    page_size = request.session.get('pagesize', QUESTIONS_PAGE_SIZE)
    questions = Question.objects.exclude(deleted=True).order_by(orderby)[:page_size] 
    # RISK - inner join queries
    questions = questions.select_related()
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
        }, context_instance=RequestContext(request))

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
    pagesize = request.session.get("pagesize",10)
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

            if settings.USE_PG_FTS:
                objects = Question.objects.filter(deleted=False).extra(
                    select={
                        'ranking': "ts_rank_cd(tsv, plainto_tsquery(%s), 32)",
                    },
                    where=["tsv @@ plainto_tsquery(%s)"],
                    params=[keywords],
                    select_params=[keywords]
                ).order_by('-ranking')

            elif settings.USE_SPHINX_SEARCH == True:
                #search index is now free of delete questions and answers
                #so there is not "antideleted" filtering here
                objects = Question.search.query(keywords)
                #no related selection either because we're relying on full text search here
            else:
                objects = Question.objects.filter(deleted=False).extra(where=['title like %s'], params=['%' + keywords + '%']).order_by(orderby)
                # RISK - inner join queries
                objects = objects.select_related();

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
#system to collect user actions and change content and store in the database
def create_new_answer( question=None, author=None, #service subroutine - refactor
            added_at=None, wiki=False,\
            text='', email_notify=False):
    """refactor
    non-view subroutine
    initializes the answer and revision
    and updates stuff in the corresponding question
    probably there is more Django-ish way to do it
    """

    html = sanitize_html(markdowner.convert(text))

    #create answer
    answer = Answer(
        question = question,
        author = author,
        added_at = added_at,
        wiki = wiki,
        html = html
    )
    if answer.wiki:
        answer.last_edited_by = answer.author
        answer.last_edited_at = added_at 
        answer.wikified_at = added_at 

    answer.save()

    #update question data
    question.last_activity_at = added_at 
    question.last_activity_by = author 
    question.save()
    Question.objects.update_answer_count(question)

    #update revision
    AnswerRevision.objects.create(
        answer     = answer,
        revision   = 1,
        author     = author,
        revised_at = added_at,
        summary    = CONST['default_version'],
        text       = text
    )

    #set notification/delete
    if email_notify:
        if author not in question.followed_by.all():
            question.followed_by.add(author)
    else:
        #not sure if this is necessary. ajax should take care of this...
        try:
            question.followed_by.remove(author)
        except:
            pass

def create_new_question(title=None,author=None,added_at=None, #service subroutine - refactor
                        wiki=False,tagnames=None,summary=None,
                        text=None):
    """refactor
    this is not a view saves new question and revision
    and maybe should become one of the methods on Question object?
    """
    html = sanitize_html(markdowner.convert(text))
    question = Question(
        title            = title,
        author           = author, 
        added_at         = added_at,
        last_activity_at = added_at,
        last_activity_by = author,
        wiki             = wiki,
        tagnames         = tagnames,
        html             = html,
        summary          = summary 
    )
    if question.wiki:
        question.last_edited_by = question.author
        question.last_edited_at = added_at
        question.wikified_at = added_at

    question.save()

    # create the first revision
    QuestionRevision.objects.create(
        question   = question,
        revision   = 1,
        title      = question.title,
        author     = author,
        revised_at = added_at,
        tagnames   = question.tagnames,
        summary    = CONST['default_version'],
        text       = text
    )
    return question

def upload(request):#ajax upload file to a question or answer 
    class FileTypeNotAllow(Exception):
        pass
    class FileSizeNotAllow(Exception):
        pass
    class UploadPermissionNotAuthorized(Exception):
        pass

    #<result><msg><![CDATA[%s]]></msg><error><![CDATA[%s]]></error><file_url>%s</file_url></result>
    xml_template = "<result><msg><![CDATA[%s]]></msg><error><![CDATA[%s]]></error><file_url>%s</file_url></result>"

    try:
        f = request.FILES['file-upload']
        # check upload permission
        if not auth.can_upload_files(request.user):
            raise UploadPermissionNotAuthorized

        # check file type
        file_name_suffix = os.path.splitext(f.name)[1].lower()
        if not file_name_suffix in settings.ALLOW_FILE_TYPES:
            raise FileTypeNotAllow

        # generate new file name
        new_file_name = str(time.time()).replace('.', str(random.randint(0,100000))) + file_name_suffix
        # use default storage to store file
        default_storage.save(new_file_name, f)
        # check file size
        # byte
        size = default_storage.size(new_file_name)
        if size > settings.ALLOW_MAX_FILE_SIZE:
            default_storage.delete(new_file_name)
            raise FileSizeNotAllow

        result = xml_template % ('Good', '', default_storage.url(new_file_name))
    except UploadPermissionNotAuthorized:
        result = xml_template % ('', _('uploading images is limited to users with >60 reputation points'), '')
    except FileTypeNotAllow:
        result = xml_template % ('', _("allowed file types are 'jpg', 'jpeg', 'gif', 'bmp', 'png', 'tiff'"), '')
    except FileSizeNotAllow:
        result = xml_template % ('', _("maximum upload file size is %sK") % settings.ALLOW_MAX_FILE_SIZE / 1024, '')
    except Exception:
        result = xml_template % ('', _('Error uploading file. Please contact the site administrator. Thank you. %s' % Exception), '')

    return HttpResponse(result, mimetype="application/xml")

#@login_required #actually you can post anonymously, but then must register
def ask(request):#view used to ask a new question
    """a view to ask a new question
    gives space for q title, body, tags and checkbox for to post as wiki

    user can start posting a question anonymously but then
    must login/register in order for the question go be shown
    """
    if request.method == "POST":
        form = AskForm(request.POST)
        if form.is_valid():

            added_at = datetime.datetime.now()
            title = strip_tags(form.cleaned_data['title'].strip())
            wiki = form.cleaned_data['wiki']
            tagnames = form.cleaned_data['tags'].strip()
            text = form.cleaned_data['text']
            html = sanitize_html(markdowner.convert(text))
            summary = strip_tags(html)[:120]

            if request.user.is_authenticated():
                author = request.user 

                question = create_new_question(
                    title            = title,
                    author           = author, 
                    added_at         = added_at,
                    wiki             = wiki,
                    tagnames         = tagnames,
                    summary          = summary,
                    text = text
                )

                return HttpResponseRedirect(question.get_absolute_url())
            else:
                request.session.flush()
                session_key = request.session.session_key
                question = AnonymousQuestion(
                    session_key = session_key,
                    title       = title,
                    tagnames = tagnames,
                    wiki = wiki,
                    text = text,
                    summary = summary,
                    added_at = added_at,
                    ip_addr = request.META['REMOTE_ADDR'],
                )
                question.save()
                return HttpResponseRedirect(reverse('user_signin_new_question'))
    else:
        form = AskForm()

    tags = _get_tags_cache_json()
    return render_to_response('ask.html', {
        'form' : form,
        'tags' : tags,
        'email_validation_faq_url':reverse('faq') + '#validate',
        }, context_instance=RequestContext(request))

@login_required
def close(request, id):#close question
    """view to initiate and process 
    question close
    """
    question = get_object_or_404(Question, id=id)
    if not auth.can_close_question(request.user, question):
        return HttpResponse('Permission denied.')
    if request.method == 'POST':
        form = CloseForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            question.closed = True
            question.closed_by = request.user
            question.closed_at = datetime.datetime.now()
            question.close_reason = reason
            question.save()
        return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = CloseForm()
        return render_to_response('close.html', {
            'form' : form,
            'question' : question,
            }, context_instance=RequestContext(request))

@login_required
def reopen(request, id):#re-open question
    """view to initiate and process 
    question close
    """
    question = get_object_or_404(Question, id=id)
    # open question
    if not auth.can_reopen_question(request.user, question):
        return HttpResponse('Permission denied.')
    if request.method == 'POST' :
        Question.objects.filter(id=question.id).update(closed=False,
            closed_by=None, closed_at=None, close_reason=None)
        return HttpResponseRedirect(question.get_absolute_url())
    else:
        return render_to_response('reopen.html', {
            'question' : question,
            }, context_instance=RequestContext(request))

@login_required
def edit_question(request, id):#edit or retag a question
    """view to edit question
    """
    question = get_object_or_404(Question, id=id)
    if question.deleted and not auth.can_view_deleted_post(request.user, question):
        raise Http404
    if auth.can_edit_post(request.user, question):
        return _edit_question(request, question)
    elif auth.can_retag_questions(request.user):
        return _retag_question(request, question)
    else:
        raise Http404

def _retag_question(request, question):#non-url subview of edit question - just retag
    """retag question sub-view used by
    view "edit_question"
    """
    if request.method == 'POST':
        form = RetagQuestionForm(question, request.POST)
        if form.is_valid():
            if form.has_changed():
                latest_revision = question.get_latest_revision()
                retagged_at = datetime.datetime.now()
                # Update the Question itself
                Question.objects.filter(id=question.id).update(
                    tagnames         = form.cleaned_data['tags'],
                    last_edited_at   = retagged_at,
                    last_edited_by   = request.user,
                    last_activity_at = retagged_at,
                    last_activity_by = request.user
                )
                # Update the Question's tag associations
                tags_updated = Question.objects.update_tags(question,
                    form.cleaned_data['tags'], request.user)
                # Create a new revision
                QuestionRevision.objects.create(
                    question   = question,
                    title      = latest_revision.title,
                    author     = request.user,
                    revised_at = retagged_at,
                    tagnames   = form.cleaned_data['tags'],
                    summary    = CONST['retagged'],
                    text       = latest_revision.text
                )
                # send tags updated singal
                tags_updated.send(sender=question.__class__, question=question)

            return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = RetagQuestionForm(question)
    return render_to_response('question_retag.html', {
        'question': question,
        'form' : form,
        'tags' : _get_tags_cache_json(),
    }, context_instance=RequestContext(request))

def _edit_question(request, question):#non-url subview of edit_question - just edit the body/title
    latest_revision = question.get_latest_revision()
    revision_form = None
    if request.method == 'POST':
        if 'select_revision' in request.POST:
            # user has changed revistion number
            revision_form = RevisionForm(question, latest_revision, request.POST)
            if revision_form.is_valid():
                # Replace with those from the selected revision
                form = EditQuestionForm(question,
                    QuestionRevision.objects.get(question=question,
                        revision=revision_form.cleaned_data['revision']))
            else:
                form = EditQuestionForm(question, latest_revision, request.POST)
        else:
            # Always check modifications against the latest revision
            form = EditQuestionForm(question, latest_revision, request.POST)
            if form.is_valid():
                html = sanitize_html(markdowner.convert(form.cleaned_data['text']))
                if form.has_changed():
                    edited_at = datetime.datetime.now()
                    tags_changed = (latest_revision.tagnames !=
                                    form.cleaned_data['tags'])
                    tags_updated = False
                    # Update the Question itself
                    updated_fields = {
                        'title': form.cleaned_data['title'],
                        'last_edited_at': edited_at,
                        'last_edited_by': request.user,
                        'last_activity_at': edited_at,
                        'last_activity_by': request.user,
                        'tagnames': form.cleaned_data['tags'],
                        'summary': strip_tags(html)[:120],
                        'html': html,
                    }

                    # only save when it's checked
                    # because wiki doesn't allow to be edited if last version has been enabled already
                    # and we make sure this in forms.
                    if ('wiki' in form.cleaned_data and
                        form.cleaned_data['wiki']):
                        updated_fields['wiki'] = True
                        updated_fields['wikified_at'] = edited_at

                    Question.objects.filter(
                        id=question.id).update(**updated_fields)
                    # Update the Question's tag associations
                    if tags_changed:
                        tags_updated = Question.objects.update_tags(
                            question, form.cleaned_data['tags'], request.user)
                    # Create a new revision
                    revision = QuestionRevision(
                        question   = question,
                        title      = form.cleaned_data['title'],
                        author     = request.user,
                        revised_at = edited_at,
                        tagnames   = form.cleaned_data['tags'],
                        text       = form.cleaned_data['text'],
                    )
                    if form.cleaned_data['summary']:
                        revision.summary = form.cleaned_data['summary']
                    else:
                        revision.summary = 'No.%s Revision' % latest_revision.revision
                    revision.save()

                return HttpResponseRedirect(question.get_absolute_url())
    else:

        revision_form = RevisionForm(question, latest_revision)
        form = EditQuestionForm(question, latest_revision)
    return render_to_response('question_edit.html', {
        'question': question,
        'revision_form': revision_form,
        'form' : form,
        'tags' : _get_tags_cache_json()
    }, context_instance=RequestContext(request))

@login_required
def edit_answer(request, id):
    answer = get_object_or_404(Answer, id=id)
    if answer.deleted and not auth.can_view_deleted_post(request.user, answer):
        raise Http404
    elif not auth.can_edit_post(request.user, answer):
        raise Http404
    else:
        latest_revision = answer.get_latest_revision()
        if request.method == "POST":
            if 'select_revision' in request.POST:
                # user has changed revistion number
                revision_form = RevisionForm(answer, latest_revision, request.POST)
                if revision_form.is_valid():
                    # Replace with those from the selected revision
                    form = EditAnswerForm(answer,
                                          AnswerRevision.objects.get(answer=answer,
                                          revision=revision_form.cleaned_data['revision']))
                else:
                    form = EditAnswerForm(answer, latest_revision, request.POST)
            else:
                form = EditAnswerForm(answer, latest_revision, request.POST)
                if form.is_valid():
                    html = sanitize_html(markdowner.convert(form.cleaned_data['text']))
                    if form.has_changed():
                        edited_at = datetime.datetime.now()
                        updated_fields = {
                            'last_edited_at': edited_at,
                            'last_edited_by': request.user,
                            'html': html,
                        }
                        Answer.objects.filter(id=answer.id).update(**updated_fields)

                        revision = AnswerRevision(
                                                  answer=answer,
                                                  author=request.user,
                                                  revised_at=edited_at,
                                                  text=form.cleaned_data['text']
                                                  )

                        if form.cleaned_data['summary']:
                            revision.summary = form.cleaned_data['summary']
                        else:
                            revision.summary = 'No.%s Revision' % latest_revision.revision
                        revision.save()

                        answer.question.last_activity_at = edited_at
                        answer.question.last_activity_by = request.user
                        answer.question.save()

                    return HttpResponseRedirect(answer.get_absolute_url())
        else:
            revision_form = RevisionForm(answer, latest_revision)
            form = EditAnswerForm(answer, latest_revision)
        return render_to_response('answer_edit.html', {
                                  'answer': answer,
                                  'revision_form': revision_form,
                                  'form': form,
                                  }, context_instance=RequestContext(request))


def answer(request, id):#process a new answer
    question = get_object_or_404(Question, id=id)
    if request.method == "POST":
        form = AnswerForm(question, request.user, request.POST)
        if form.is_valid():
            wiki = form.cleaned_data['wiki']
            text = form.cleaned_data['text']
            update_time = datetime.datetime.now()

            if request.user.is_authenticated():
                create_new_answer(
                                  question=question,
                                  author=request.user,
                                  added_at=update_time,
                                  wiki=wiki,
                                  text=text,
                                  email_notify=form.cleaned_data['email_notify']
                                  )
            else:
                request.session.flush()
                html = sanitize_html(markdowner.convert(text))
                summary = strip_tags(html)[:120]
                anon = AnonymousAnswer(
                                       question=question,
                                       wiki=wiki,
                                       text=text,
                                       summary=summary,
                                       session_key=request.session.session_key,
                                       ip_addr=request.META['REMOTE_ADDR'],
                                       )
                anon.save()
                return HttpResponseRedirect(reverse('user_signin_new_answer'))

    return HttpResponseRedirect(question.get_absolute_url())

def vote(request, id):#refactor - pretty incomprehensible view used by various ajax calls
#issues: this subroutine is too long, contains many magic numbers and other issues
#it's called "vote" but many actions processed here have nothing to do with voting
    """
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

    accept answer code:
        response_data['allowed'] = -1, Accept his own answer   0, no allowed - Anonymous    1, Allowed - by default
        response_data['success'] =  0, failed                                               1, Success - by default
        response_data['status']  =  0, By default                                           1, Answer has been accepted already(Cancel)

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

    def __can_vote(vote_score, user):#refactor - belongs to auth.py
        if vote_score == 1:#refactor magic number
            return auth.can_vote_up(request.user)
        else:
            return auth.can_vote_down(request.user)

    try:
        if not request.user.is_authenticated():
            response_data['allowed'] = 0
            response_data['success'] = 0

        elif request.is_ajax():
            question = get_object_or_404(Question, id=id)
            vote_type = request.POST.get('type')

            #accept answer
            if vote_type == '0':
                answer_id = request.POST.get('postId')
                answer = get_object_or_404(Answer, id=answer_id)
                # make sure question author is current user
                if question.author == request.user:
                    # answer user who is also question author is not allow to accept answer
                    if answer.author == question.author:
                        response_data['success'] = 0
                        response_data['allowed'] = -1
                    # check if answer has been accepted already
                    elif answer.accepted:
                        onAnswerAcceptCanceled(answer, request.user)
                        response_data['status'] = 1
                    else:
                        # set other answers in this question not accepted first
                        for answer_of_question in Answer.objects.get_answers_from_question(question, request.user):
                            if answer_of_question != answer and answer_of_question.accepted:
                                onAnswerAcceptCanceled(answer_of_question, request.user)

                        #make sure retrieve data again after above author changes, they may have related data
                        answer = get_object_or_404(Answer, id=answer_id)
                        onAnswerAccept(answer, request.user)
                else:
                    response_data['allowed'] = 0
                    response_data['success'] = 0
            # favorite
            elif vote_type == '4':
                has_favorited = False
                fav_questions = FavoriteQuestion.objects.filter(question=question)
                # if the same question has been favorited before, then delete it
                if fav_questions is not None:
                    for item in fav_questions:
                        if item.user == request.user:
                            item.delete()
                            response_data['status'] = 1
                            response_data['count']  = len(fav_questions) - 1
                            if response_data['count'] < 0:
                                response_data['count'] = 0
                            has_favorited = True
                # if above deletion has not been executed, just insert a new favorite question
                if not has_favorited:
                    new_item = FavoriteQuestion(question=question, user=request.user)
                    new_item.save()
                    response_data['count']  = FavoriteQuestion.objects.filter(question=question).count()
                Question.objects.update_favorite_count(question)

            elif vote_type in ['1', '2', '5', '6']:
                post_id = id
                post = question
                vote_score = 1
                if vote_type in ['5', '6']:
                    answer_id = request.POST.get('postId')
                    answer = get_object_or_404(Answer, id=answer_id)
                    post_id = answer_id
                    post = answer
                if vote_type in ['2', '6']:
                    vote_score = -1

                if post.author == request.user:
                    response_data['allowed'] = -1
                elif not __can_vote(vote_score, request.user):
                    response_data['allowed'] = -2
                elif post.votes.filter(user=request.user).count() > 0:
                    vote = post.votes.filter(user=request.user)[0]
                    # unvote should be less than certain time
                    if (datetime.datetime.now().day - vote.voted_at.day) >= VOTE_RULES['scope_deny_unvote_days']:
                        response_data['status'] = 2
                    else:
                        voted = vote.vote
                        if voted > 0:
                            # cancel upvote
                            onUpVotedCanceled(vote, post, request.user)

                        else:
                            # cancel downvote
                            onDownVotedCanceled(vote, post, request.user)

                        response_data['status'] = 1
                        response_data['count'] = post.score
                elif Vote.objects.get_votes_count_today_from_user(request.user) >= VOTE_RULES['scope_votes_per_user_per_day']:
                    response_data['allowed'] = -3
                else:
                    vote = Vote(user=request.user, content_object=post, vote=vote_score, voted_at=datetime.datetime.now())
                    if vote_score > 0:
                        # upvote
                        onUpVoted(vote, post, request.user)
                    else:
                        # downvote
                        onDownVoted(vote, post, request.user)

                    votes_left = VOTE_RULES['scope_votes_per_user_per_day'] - Vote.objects.get_votes_count_today_from_user(request.user)
                    if votes_left <= VOTE_RULES['scope_warn_votes_left']:
                        response_data['message'] = u'%s votes left' % votes_left
                    response_data['count'] = post.score
            elif vote_type in ['7', '8']:
                post = question
                post_id = id
                if vote_type == '8':
                    post_id = request.POST.get('postId')
                    post = get_object_or_404(Answer, id=post_id)

                if FlaggedItem.objects.get_flagged_items_count_today(request.user) >= VOTE_RULES['scope_flags_per_user_per_day']:
                    response_data['allowed'] = -3
                elif not auth.can_flag_offensive(request.user):
                    response_data['allowed'] = -2
                elif post.flagged_items.filter(user=request.user).count() > 0:
                    response_data['status'] = 1
                else:
                    item = FlaggedItem(user=request.user, content_object=post, flagged_at=datetime.datetime.now())
                    onFlaggedItem(item, post, request.user)
                    response_data['count'] = post.offensive_flag_count
                    # send signal when question or answer be marked offensive
                    mark_offensive.send(sender=post.__class__, instance=post, mark_by=request.user)
            elif vote_type in ['9', '10']:
                post = question
                post_id = id
                if vote_type == '10':
                    post_id = request.POST.get('postId')
                    post = get_object_or_404(Answer, id=post_id)

                if not auth.can_delete_post(request.user, post):
                    response_data['allowed'] = -2
                elif post.deleted == True:
                    logging.debug('debug restoring post in view')
                    onDeleteCanceled(post, request.user)
                    response_data['status'] = 1
                else:
                    onDeleted(post, request.user)
                    delete_post_or_answer.send(sender=post.__class__, instance=post, delete_by=request.user)
            elif vote_type == '11':#subscribe q updates
                user = request.user
                if user.is_authenticated():
                    if user not in question.followed_by.all():
                        question.followed_by.add(user)
                        if settings.EMAIL_VALIDATION == 'on' and user.email_isvalid == False:
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
                    if user in question.followed_by.all():
                        question.followed_by.remove(user)
        else:
            response_data['success'] = 0
            response_data['message'] = u'Request mode is not supported. Please try again.'

        data = simplejson.dumps(response_data)

    except Exception, e:
        response_data['message'] = str(e)
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
def ajax_command(request):#refactor? view processing ajax commands - note "vote" and view others do it too
    if 'command' not in request.POST:
        return HttpResponseForbidden(mimetype="application/json")
    if request.POST['command'] == 'toggle-ignored-questions':
        return ajax_toggle_ignored_questions(request)

def question_comments(request, id):#ajax handler for loading comments to question
    question = get_object_or_404(Question, id=id)
    user = request.user
    return __comments(request, question, 'question')

def answer_comments(request, id):#ajax handler for loading comments on answer
    answer = get_object_or_404(Answer, id=id)
    user = request.user
    return __comments(request, answer, 'answer')

def __comments(request, obj, type):#non-view generic ajax handler to load comments to an object
    # only support get post comments by ajax now
    user = request.user
    if request.is_ajax():
        if request.method == "GET":
            response = __generate_comments_json(obj, type, user)
        elif request.method == "POST":
            if auth.can_add_comments(user,obj):
                comment_data = request.POST.get('comment')
                comment = Comment(content_object=obj, comment=comment_data, user=request.user)
                comment.save()
                obj.comment_count = obj.comment_count + 1
                obj.save()
                response = __generate_comments_json(obj, type, user)
            else:
                response = HttpResponseForbidden(mimetype="application/json")
        return response

def __generate_comments_json(obj, type, user):#non-view generates json data for the post comments
    comments = obj.comments.all().order_by('id')
    # {"Id":6,"PostId":38589,"CreationDate":"an hour ago","Text":"hello there!","UserDisplayName":"Jarrod Dixon","UserUrl":"/users/3/jarrod-dixon","DeleteUrl":null}
    json_comments = []
    from forum.templatetags.extra_tags import diff_date
    for comment in comments:
        comment_user = comment.user
        delete_url = ""
        if user != None and auth.can_delete_comment(user, comment):
            #/posts/392845/comments/219852/delete
            #todo translate this url
            delete_url = reverse(index) + type + "s/%s/comments/%s/delete/" % (obj.id, comment.id)
        json_comments.append({"id" : comment.id,
            "object_id" : obj.id,
            "comment_age" : diff_date(comment.added_at),
            "text" : comment.comment,
            "user_display_name" : comment_user.username,
            "user_url" : comment_user.get_profile_url(),
            "delete_url" : delete_url
        })

    data = simplejson.dumps(json_comments)
    return HttpResponse(data, mimetype="application/json")

def delete_comment(request, object_id='', comment_id='', commented_object_type=None):#ajax handler to delete comment
    response = None
    commented_object = None
    if commented_object_type == 'question':
        commented_object = Question
    elif commented_object_type == 'answer':
        commented_object = Answer

    if request.is_ajax():
        comment = get_object_or_404(Comment, id=comment_id)
        if auth.can_delete_comment(request.user, comment):
            obj = get_object_or_404(commented_object, id=object_id)
            obj.comments.remove(comment)
            obj.comment_count = obj.comment_count - 1
            obj.save()
            user = request.user
            return __generate_comments_json(obj, commented_object_type, user)
    raise PermissionDenied()

