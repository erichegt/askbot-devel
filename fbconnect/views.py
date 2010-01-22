from django.shortcuts import render_to_response as render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login,  logout
from models import FBAssociation
from forum.forms import EditUserEmailFeedsForm
from django.conf import settings

import fb
import forms

import logging        

def signin(request,  newquestion = False,  newanswer = False):
    state,  context = fb.get_user_state(request)
    
    if state == fb.STATES['FIRSTTIMER']:
        if newquestion:
            register_url = 'fb_user_register_new_question'
        elif newanswer:
            register_url = 'fb_user_register_new_answer'
        else:
            register_url = 'fb_user_register'
        return HttpResponseRedirect(reverse(register_url))
    elif state == fb.STATES['RETURNINGUSER']:
        return login_and_forward(request,  context,  newquestion,  newanswer)
    elif state == fb.STATES['SESSIONEXPIRED']:
        response = logout(request,  next_page=reverse('index'))
        fb.delete_cookies(response)
        return response
        
    return HttpResponseRedirect(reverse('index'))
    
def register(request,  newquestion = False,  newanswer = False):
    state,  context = fb.get_user_state(request)
    
    if state == fb.STATES['FIRSTTIMER']:
        
        if 'bnewaccount' in request.POST.keys():
            form1 = forms.FBConnectRegisterForm(request.POST)
            email_feeds_form = EditUserEmailFeedsForm(request.POST)
            
            if (form1.is_valid() and email_feeds_form.is_valid()):
                tmp_pwd = User.objects.make_random_password()
                user_ = User.objects.create_user(form1.cleaned_data['username'],
                         form1.cleaned_data['email'], tmp_pwd)

                user_.set_unusable_password()
                
                uassoc = FBAssociation(user=user_,  fbuid=context['uid'])
                uassoc.save()
                
                email_feeds_form.save(user_)
                
                return login_and_forward(request,  user_,  newquestion,  newanswer)
        else:            
            form1 = forms.FBConnectRegisterForm(initial={
                'next': '/',
                'username': context['name'],
                'email': '',
            }) 
            
            email_feeds_form = EditUserEmailFeedsForm()

        return render('authopenid/complete.html', {
            'form1': form1,
            'email_feeds_form': email_feeds_form,
            'provider':mark_safe('facebook'),
            'login_type':'facebook',
            'gravatar_faq_url':reverse('faq') + '#gravatar',
        }, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('index'))
        
def login_and_forward(request,  user,  newquestion = False,  newanswer = False):
    old_session = request.session.session_key
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request,  user)
    
    from forum.models import user_logged_in
    user_logged_in.send(user=user,session_key=old_session,sender=None)
    
    if (newquestion):
        from forum.models import Question
        question = Question.objects.filter(author=user).order_by('-added_at')[0]
        return HttpResponseRedirect(question.get_absolute_url())
        
    if (newanswer):
        from forum.models import Answer
        answer = Answer.objects.filter(author=user).order_by('-added_at')[0]
        return HttpResponseRedirect(answer.get_absolute_url())
        
    return HttpResponseRedirect('/')
    
