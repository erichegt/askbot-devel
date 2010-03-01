from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.html import *

from models import *

from forum.forms import AskForm
from forum.views.readers import _get_tags_cache_json
from forum.models import *
from forum.utils.html import sanitize_html

def books(request):
    return HttpResponseRedirect(reverse('books') + '/mysql-zhaoyang')

def book(request, short_name, unanswered=False):
    """
    1. questions list
    2. book info
    3. author info and blog rss items
    """
    """
    List of Questions, Tagged questions, and Unanswered questions.
    """
    books = Book.objects.extra(where=['short_name = %s'], params=[short_name])
    match_count = len(books)
    if match_count == 0:
        raise Http404
    else:
        # the book info
        book = books[0]
        # get author info
        author_info = BookAuthorInfo.objects.get(book=book)
        # get author rss info
        author_rss = BookAuthorRss.objects.filter(book=book)

        # get pagesize from session, if failed then get default value
        user_page_size = request.session.get("pagesize", QUESTIONS_PAGE_SIZE)
        # set pagesize equal to logon user specified value in database
        if request.user.is_authenticated() and request.user.questions_per_page > 0:
            user_page_size = request.user.questions_per_page

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        view_id = request.GET.get('sort', None)
        view_dic = {"latest":"-added_at", "active":"-last_activity_at", "hottest":"-answer_count", "mostvoted":"-score" }
        try:
            orderby = view_dic[view_id]
        except KeyError:
            view_id = "latest"
            orderby = "-added_at"

        # check if request is from tagged questions
        if unanswered:
            # check if request is from unanswered questions
            # Article.objects.filter(publications__id__exact=1)
            objects = Question.objects.filter(book__id__exact=book.id, deleted=False, answer_count=0).order_by(orderby)
        else:
            objects = Question.objects.filter(book__id__exact=book.id, deleted=False).order_by(orderby)

        # RISK - inner join queries
        objects = objects.select_related();
        objects_list = Paginator(objects, user_page_size)
        questions = objects_list.page(page)

        return render_to_response('book.html', {
            "book" : book,
            "author_info" : author_info,
            "author_rss" : author_rss,
            "questions" : questions,
            "context" : {
                'is_paginated' : True,
                'pages': objects_list.num_pages,
                'page': page,
                'has_previous': questions.has_previous(),
                'has_next': questions.has_next(),
                'previous': questions.previous_page_number(),
                'next': questions.next_page_number(),
                'base_url' : request.path + '?sort=%s&' % view_id,
                'pagesize' : user_page_size
            }
        }, context_instance=RequestContext(request))

@login_required
def ask_book(request, short_name):
    if request.method == "POST":
        form = AskForm(request.POST)
        if form.is_valid():
            added_at = datetime.datetime.now()
            html = sanitize_html(markdowner.convert(form.cleaned_data['text']))
            question = Question(
                title            = strip_tags(form.cleaned_data['title']),
                author           = request.user,
                added_at         = added_at,
                last_activity_at = added_at,
                last_activity_by = request.user,
                wiki             = form.cleaned_data['wiki'],
                tagnames         = form.cleaned_data['tags'].strip(),
                html             = html,
                summary          = strip_tags(html)[:120]
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
                author     = request.user,
                revised_at = added_at,
                tagnames   = question.tagnames,
                summary    = CONST['default_version'],
                text       = form.cleaned_data['text']
            )

            books = Book.objects.extra(where=['short_name = %s'], params=[short_name])
            match_count = len(books)
            if match_count == 1:
                # the book info
                book = books[0]
                book.questions.add(question)

            return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = AskForm()

    tags = _get_tags_cache_json()
    return render_to_response('ask.html', {
        'form' : form,
        'tags' : tags,
        'email_validation_faq_url': reverse('faq') + '#validate',
        }, context_instance=RequestContext(request))