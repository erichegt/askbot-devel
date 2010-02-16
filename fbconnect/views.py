from django.shortcuts import render_to_response as render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login,  logout
from models import FBAssociation
from forum.forms import SimpleEmailSubscribeForm
from django.conf import settings

import fb
import forms

import logging        

def signin(request,  newquestion = False,  newanswer = False):
    logging.debug('')
    state,  context = fb.get_user_state(request)
    
    if state == fb.STATES['FIRSTTIMER']:
        logging.debug('FB state = FIRSTTIMER')
        if newquestion:
            register_url = 'fb_user_register_new_question'
        elif newanswer:
            register_url = 'fb_user_register_new_answer'
        else:
            register_url = 'fb_user_register'
        return HttpResponseRedirect(reverse(register_url))
    elif state == fb.STATES['RETURNINGUSER']:
        logging.debug('FB state = RETURNINGUSER')
        return login_and_forward(request,  context,  newquestion,  newanswer)
    elif state == fb.STATES['SESSIONEXPIRED']:
        logging.debug('FB state = SESSIONEXPIRED')
        response = logout(request,  next_page=reverse('index'))
        fb.delete_cookies(response)
        return response
        
    return HttpResponseRedirect(reverse('index'))
    
def register(request,  newquestion = False,  newanswer = False):
    logging.debug('')
    state,  context = fb.get_user_state(request)
    
    if state == fb.STATES['FIRSTTIMER']:
        logging.debug('FB FIRSTTIMER - try to register locally')
        logging.debug('request method is %s' % request.method)
        if request.method == 'POST' and 'bnewaccount' in request.POST:
            form1 = forms.FBConnectRegisterForm(request.POST)
            email_feeds_form = SimpleEmailSubscribeForm(request.POST)
            
            if (form1.is_valid() and email_feeds_form.is_valid()):
                tmp_pwd = User.objects.make_random_password()
                user_ = User.objects.create_user(form1.cleaned_data['username'],
                         form1.cleaned_data['email'], tmp_pwd)
                
                user_.set_unusable_password()
                logging.debug('created new internal user %s' % form1.cleaned_data['username'])
                
                uassoc = FBAssociation(user=user_,  fbuid=context['uid'])
                uassoc.save()
                logging.debug('created new user association')
                
                email_feeds_form.save(user_)
                
                return login_and_forward(request,  user_,  newquestion,  newanswer)
            else:
                logging.debug('form user input is invalid')
        else:            
            form1 = forms.FBConnectRegisterForm(initial={
                'next': '/',
                'username': context['name'],
                'email': '',
            }) 
            email_feeds_form = SimpleEmailSubscribeForm()
        
        return render('authopenid/complete.html', {
            'form1': form1,
            'email_feeds_form': email_feeds_form,
            'provider':mark_safe('facebook'),
            'login_type':'facebook',
            'gravatar_faq_url':reverse('faq') + '#gravatar',
        }, context_instance=RequestContext(request))
    else:
        logging.debug('not a FIRSTTIMER --> redirect to index view')
        return HttpResponseRedirect(reverse('index'))
        
def login_and_forward(request,  user,  newquestion = False,  newanswer = False):
    old_session = request.session.session_key
    user.backend = "django.contrib.auth.backends.ModelBackend"
    logging.debug('attached auth.backends.ModelBackend to this FB user')
    login(request,  user)
    logging.debug('user logged in!')
    
    from forum.models import user_logged_in
    user_logged_in.send(user=user,session_key=old_session,sender=None)
    logging.debug('user_logged_in signal sent')
    
    if (newquestion):
        from forum.models import Question
        question = Question.objects.filter(author=user).order_by('-added_at')[0]
        logging.debug('redirecting to newly posted question')
        return HttpResponseRedirect(question.get_absolute_url())
        
    if (newanswer):
        from forum.models import Answer
        answer = Answer.objects.filter(author=user).order_by('-added_at')[0]
        logging.debug('redirecting to newly posted answer')
        return HttpResponseRedirect(answer.get_absolute_url())
        
    logging.debug('redirecting to front page')
    return HttpResponseRedirect('/')
