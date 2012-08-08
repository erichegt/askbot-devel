from datetime import datetime

from django.views.decorators import csrf
from django.shortcuts import redirect
from django.utils import simplejson
from django.contrib.auth.models import User
from django.core import exceptions

from django.contrib.auth.decorators import login_required

from askbot.skins.loaders import render_into_skin
from askbot import models
from askbot import forms

@csrf.csrf_protect
def ask_widget(request):

    def post_question(data, request):
        thread = models.Thread.objects.create_new(**data_dict)
        question = thread._question_post()
        request.session['widget_question_url'] = question.get_absolute_url()
        return question


    if request.method == "POST":
        form = forms.AskWidgetForm(request.POST)
        if form.is_valid():
            ask_anonymously = form.cleaned_data['ask_anonymously']
            title = form.cleaned_data['title']
            data_dict = {
                         'title': title,
                         'added_at': datetime.now(),
                         'wiki': False,
                         'text': ' ',
                         'tagnames': '',
                         'is_anonymous': ask_anonymously
                        }
            if request.user.is_authenticated():
                data_dict['author'] = request.user
                question = post_question(data_dict, request)
                return redirect('ask_by_widget_complete')
            else:
                request.session['widget_question'] = data_dict
                return redirect('widget_signin')
                #return redirect('user_signin',
                #        **{'template_name': 'authopenid/widget_signin.html'})
    else:
        if 'widget_question' in request.session and \
                request.GET.get('action', 'post-after-login'):
            if request.user.is_authenticated():
                data_dict = request.session['widget_question']
                data_dict['author'] = request.user
                question = post_question(request.session['widget_question'], request)
                del request.session['widget_question']
                return redirect('ask_by_widget_complete')
            else:
                #FIXME: this redirect is temporal need to create the correct view
                return redirect('widget_signin')
                #return redirect('user_signin',
                #        **{'template_name': 'authopenid/widget_signin.html'})

        form = forms.AskWidgetForm()
    data = {'form': form}
    return render_into_skin('ask_by_widget.html', data, request)

@login_required
def ask_widget_complete(request):
    question_url = request.session.get('widget_question_url')
    if question_url:
        del request.session['widget_question_url']
    else:
        question_url = '#'

    data = {'question_url': question_url}
    return render_into_skin('ask_widget_complete.html', data, request)
