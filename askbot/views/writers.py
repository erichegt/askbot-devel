# encoding:utf-8
import os.path
import time, datetime, random
from django.core.files.storage import default_storage
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.conf import settings

from askbot import auth
from askbot.views.readers import _get_tags_cache_json
from askbot import forms
from askbot import models

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
        form = forms.AskForm(request.POST)
        if form.is_valid():

            added_at = datetime.datetime.now()
            #todo: move this to clean_title
            title = form.cleaned_data['title'].strip()
            wiki = form.cleaned_data['wiki']
            #todo: move this to clean_tagnames
            tagnames = form.cleaned_data['tags'].strip()
            text = form.cleaned_data['text']

            #todo: move this to AskForm.clean_text
            #todo: make custom MarkDownField
            text = form.cleaned_data['text']

            if request.user.is_authenticated():
                author = request.user 

                question = models.Question.objects.create_new(
                    title            = title,
                    author           = author, 
                    added_at         = added_at,
                    wiki             = wiki,
                    tagnames         = tagnames,
                    text = text,
                )

                return HttpResponseRedirect(question.get_absolute_url())
            else:
                request.session.flush()
                session_key = request.session.session_key
                summary = strip_tags(text)[:120]
                question = models.AnonymousQuestion(
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
        #this branch is for the initial load of ask form
        form = forms.AskForm()
        if 'title' in request.GET:
            #normally this title is inherited from search query
            #but it is possible to ask with a parameter title in the url query
            form.initial['title'] = request.GET['title']
        else:
            #attempt to extract title from previous search query
            search_state = request.session.get('search_state',None)
            if search_state:
                query = search_state.query
                form.initial['title'] = query

    tags = _get_tags_cache_json()
    return render_to_response('ask.html', {
        'active_tab': 'ask',
        'form' : form,
        'tags' : tags,
        'email_validation_faq_url':reverse('faq') + '#validate',
        }, context_instance=RequestContext(request))

@login_required
def edit_question(request, id):#edit or retag a question
    """view to edit question
    """
    question = get_object_or_404(models.Question, id=id)
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
        form = forms.RetagQuestionForm(question, request.POST)
        if form.is_valid():
            if form.has_changed():
                question.retag(
                    retagged_by = request.user,
                    retagged_at = datetime.datetime.now(),
                    tagnames = form.cleaned_data['tags'],
                )
            return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = forms.RetagQuestionForm(question)
    return render_to_response('question_retag.html', {
        'active_tab': 'questions',
        'question': question,
        'form' : form,
        'tags' : _get_tags_cache_json(),
    }, context_instance=RequestContext(request))

def _edit_question(request, question):#non-url subview of edit_question - just edit the body/title
    latest_revision = question.get_latest_revision()
    revision_form = None
    if request.method == 'POST':
        if 'select_revision' in request.POST:#revert-type edit
            # user has changed revistion number
            revision_form = forms.RevisionForm(question, latest_revision, request.POST)
            if revision_form.is_valid():
                # Replace with those from the selected revision
                form = forms.EditQuestionForm(question,
                    models.QuestionRevision.objects.get(question=question,
                        revision=revision_form.cleaned_data['revision']))
            else:
                form = forms.EditQuestionForm(question, latest_revision, request.POST)
        else:#new content edit
            # Always check modifications against the latest revision
            form = forms.EditQuestionForm(question, latest_revision, request.POST)
            if form.is_valid():
                if form.has_changed():
                    edited_at = datetime.datetime.now()
                    edited_by = request.user
                    question.apply_edit(
                        edited_at = edited_at,
                        edited_by = edited_by,
                        title = form.cleaned_data['title'],
                        text = form.cleaned_data['text'],
                        #todo: summary name clash in question and question revision
                        comment = form.cleaned_data['summary'],
                        tags = form.cleaned_data['tags'],
                        wiki = form.cleaned_data.get('wiki',False),
                    )

                return HttpResponseRedirect(question.get_absolute_url())
    else:
        revision_form = forms.RevisionForm(question, latest_revision)
        form = forms.EditQuestionForm(question, latest_revision)
    return render_to_response('question_edit.html', {
        'active_tab': 'questions',
        'question': question,
        'revision_form': revision_form,
        'form' : form,
        'tags' : _get_tags_cache_json()
    }, context_instance=RequestContext(request))

@login_required
def edit_answer(request, id):
    answer = get_object_or_404(models.Answer, id=id)
    if answer.deleted and not auth.can_view_deleted_post(request.user, answer):
        raise Http404
    elif not auth.can_edit_post(request.user, answer):
        raise Http404
    else:
        latest_revision = answer.get_latest_revision()
        if request.method == "POST":
            if 'select_revision' in request.POST:
                # user has changed revistion number
                revision_form = forms.RevisionForm(answer, latest_revision, request.POST)
                if revision_form.is_valid():
                    # Replace with those from the selected revision
                    form = forms.EditAnswerForm(answer,
                                          models.AnswerRevision.objects.get(answer=answer,
                                          revision=revision_form.cleaned_data['revision']))
                else:
                    form = forms.EditAnswerForm(answer, latest_revision, request.POST)
            else:
                form = forms.EditAnswerForm(answer, latest_revision, request.POST)
                if form.is_valid():
                    if form.has_changed():
                        edited_at = datetime.datetime.now()
                        answer.apply_edit(
                            edited_at = edited_at,
                            edited_by = request.user,
                            text = form.cleaned_data['text'],
                            comment = form.cleaned_data['summary'],
                            wiki = False,#todo: fix this there is no "wiki" field on "edit answer"
                        )
                    return HttpResponseRedirect(answer.get_absolute_url())
        else:
            revision_form = forms.RevisionForm(answer, latest_revision)
            form = forms.EditAnswerForm(answer, latest_revision)
        return render_to_response('answer_edit.html', {
                                  'active_tab': 'questions',
                                  'answer': answer,
                                  'revision_form': revision_form,
                                  'form': form,
                                  }, context_instance=RequestContext(request))

#todo: rename this function to post_new_answer
def answer(request, id):#process a new answer
    question = get_object_or_404(models.Question, id=id)
    if request.method == "POST":
        form = forms.AnswerForm(question, request.user, request.POST)
        if form.is_valid():
            wiki = form.cleaned_data['wiki']
            text = form.cleaned_data['text']
            update_time = datetime.datetime.now()

            if request.user.is_authenticated():
                models.Answer.objects.create_new(
                                  question=question,
                                  author=request.user,
                                  added_at=update_time,
                                  wiki=wiki,
                                  text=text,
                                  email_notify=form.cleaned_data['email_notify']
                                  )
            else:
                request.session.flush()
                anon = models.AnonymousAnswer(
                                       question=question,
                                       wiki=wiki,
                                       text=text,
                                       summary=strip_tags(text)[:120],
                                       session_key=request.session.session_key,
                                       ip_addr=request.META['REMOTE_ADDR'],
                                       )
                anon.save()
                return HttpResponseRedirect(reverse('user_signin_new_answer'))

    return HttpResponseRedirect(question.get_absolute_url())

def __generate_comments_json(obj, comment_type, user):
    """non-view generates json data for the post comments
    """
    comments = obj.comments.all().order_by('id')
    # {"Id":6,"PostId":38589,"CreationDate":"an hour ago","Text":"hello there!","UserDisplayName":"Jarrod Dixon","UserUrl":"/users/3/jarrod-dixon","DeleteUrl":null}
    json_comments = []
    from askbot.templatetags.extra_tags import diff_date
    for comment in comments:
        comment_user = comment.user
        delete_url = ""
        if user != None and auth.can_delete_comment(user, comment):
            #/posts/392845/comments/219852/delete
            #todo translate this url
            delete_url = reverse('index') + comment_type + \
                            "s/%s/comments/%s/delete/" % (obj.id, comment.id)
        json_comments.append({"id" : comment.id,
            "object_id" : obj.id,
            "comment_age" : diff_date(comment.added_at),
            "text" : comment.html,
            "user_display_name" : comment_user.username,
            "user_url" : comment_user.get_profile_url(),
            "delete_url" : delete_url
        })

    data = simplejson.dumps(json_comments)
    return HttpResponse(data, mimetype="application/json")

def question_comments(request, id):#ajax handler for loading comments to question
    question = get_object_or_404(models.Question, id=id)
    return __comments(request, question, 'question')

def answer_comments(request, id):#ajax handler for loading comments on answer
    answer = get_object_or_404(models.Answer, id=id)
    return __comments(request, answer, 'answer')

def __comments(request, obj, comment_type):#non-view generic ajax handler to load comments to an object
    # only support get post comments by ajax now
    user = request.user
    if request.is_ajax():
        if request.method == "GET":
            response = __generate_comments_json(obj, comment_type, user)
        elif request.method == "POST":
            if auth.can_add_comments(user, obj):
                obj.add_comment(
                    comment = request.POST.get('comment'),
                    user = request.user,
                )
                response = __generate_comments_json(obj, comment_type, user)
            else:
                response = HttpResponseForbidden(mimetype="application/json")
        return response

def delete_comment(request, object_id='', comment_id='', commented_object_type=None):#ajax handler to delete comment
    commented_object = None
    if commented_object_type == 'question':
        commented_object = models.Question
    elif commented_object_type == 'answer':
        commented_object = models.Answer

    if request.is_ajax():
        comment = get_object_or_404(models.Comment, id=comment_id)
        if auth.can_delete_comment(request.user, comment):
            obj = get_object_or_404(commented_object, id=object_id)
            obj.comments.remove(comment)
            obj.comment_count = obj.comment_count - 1
            obj.save()
            user = request.user
            return __generate_comments_json(obj, commented_object_type, user)
    raise PermissionDenied()
