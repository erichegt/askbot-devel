from datetime import datetime

from django.core import exceptions
from django.utils import simplejson
from django.template import Context
from django.http import HttpResponse
from django.views.decorators import csrf
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404

from django.contrib.auth.decorators import login_required

from askbot.skins.loaders import render_into_skin, get_template
from askbot.utils import decorators
from askbot import models
from askbot import forms


@decorators.admins_only
def widgets(request):
    data = {
        'ask_widgets': models.AskWidget.objects.all(),
        'page_class': 'widgets'
    }
    return render_into_skin('widgets.html', data, request)

@csrf.csrf_protect
def ask_widget(request, widget_id):

    def post_question(data, request):
        thread = models.Thread.objects.create_new(**data)
        question = thread._question_post()
        request.session['widget_question_url'] = question.get_absolute_url()
        return question

    widget = get_object_or_404(models.AskWidget, id=widget_id)

    if request.method == "POST":
        form = forms.AskWidgetForm(include_text=widget.include_text_field,
                data=request.POST)
        if form.is_valid():
            ask_anonymously = form.cleaned_data['ask_anonymously']
            title = form.cleaned_data['title']
            if widget.include_text_field:
                text = form.cleaned_data['text']
            else:
                text = ' '
            data_dict = {
                'title': title,
                'added_at': datetime.now(),
                'wiki': False,
                'text': text,
                'tagnames': '',
                'is_anonymous': ask_anonymously
            }
            if request.user.is_authenticated():
                data_dict['author'] = request.user
                question = post_question(data_dict, request)
                return redirect('ask_by_widget_complete')
            else:
                request.session['widget_question'] = data_dict
                next_url = '%s?next=%s' % (reverse('widget_signin'),
                        reverse('ask_by_widget', args=(widget.id,)))
                return redirect(next_url)
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
                next_url = '%s?next=%s' % (reverse('widget_signin'), reverse('ask_by_widget'))
                return redirect(next_url)

        form = forms.AskWidgetForm(include_text=widget.include_text_field)

    data = {'form': form, 'widget': widget}
    return render_into_skin('ask_by_widget.html', data, request)

@login_required
def ask_widget_complete(request):
    question_url = request.session.get('widget_question_url')
    custom_css = request.session.get('widget_css')
    if question_url:
        del request.session['widget_question_url']
    else:
        question_url = '#'

    if custom_css:
        del request.session['widget_css']

    data = {'question_url': question_url, 'custom_css': custom_css}
    return render_into_skin('ask_widget_complete.html', data, request)


@decorators.admins_only
def list_ask_widget(request):
    widgets = models.AskWidget.objects.all()
    data = {'widgets': widgets}
    return render_into_skin('list_ask_widget.html', data, request)

@decorators.admins_only
def create_ask_widget(request):
    if request.method=='POST':
        form = models.widgets.CreateAskWidgetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_ask_widgets')
    else:
        form = models.widgets.CreateAskWidgetForm()

    data = {'form': form}
    return render_into_skin('ask_widget_form.html', data, request)

@decorators.admins_only
def edit_ask_widget(request, widget_id):
    widget = get_object_or_404(models.AskWidget, pk=widget_id)
    if request.method=='POST':
        form = models.widgets.CreateAskWidgetForm(request.POST,
                instance=widget)
        if form.is_valid():
            form.save()
            return redirect('list_ask_widgets')
    else:
        form = models.widgets.CreateAskWidgetForm(instance=widget)

    data = {'form': form}
    return render_into_skin('ask_widget_form.html', data, request)

@decorators.admins_only
def delete_ask_widget(request, widget_id):
    widget = get_object_or_404(models.AskWidget, pk=widget_id)
    if request.method=="POST":
        widget.delete()
        return redirect('list_ask_widgets')
    else:
        return render_into_skin('delete_ask_widget.html',
                {'widget': widget}, request)

#TODO: Add cache
def render_ask_widget_js(request, widget_id):
    widget = get_object_or_404(models.AskWidget)
    content_tpl =  get_template('widgets/askbot_widget.js', request)
    context_dict = {'widget': widget, 'host': request.get_host()}
    content =  content_tpl.render(Context(context_dict))
    print content
    return HttpResponse(content, mimetype='text/javascript')
