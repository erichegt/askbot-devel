from django.shortcuts import render_to_response as render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import login
from models import FBAssociation
from forum.forms import EditUserEmailFeedsForm
from django.conf import settings

import fb
import forms

import logging        

def signin(request):
    user_state = fb.get_user_state(request)
    
    if user_state == fb.STATES['FIRSTTIMER']:
        return HttpResponseRedirect(reverse('fb_user_register'))
    
    return HttpResponseRedirect('/')
    
def register(request):
    if fb.get_user_state(request) == fb.STATES['FIRSTTIMER']:
        user_data = fb.get_user_data(request.COOKIES)
        
        if 'bnewaccount' in request.POST.keys():
            form1 = forms.FBConnectRegisterForm(request.POST)
            email_feeds_form = EditUserEmailFeedsForm(request.POST)
            
            if (form1.is_valid() and email_feeds_form.is_valid()):
                tmp_pwd = User.objects.make_random_password()
                user_ = User.objects.create_user(form1.cleaned_data['username'],
                         form1.cleaned_data['email'], tmp_pwd)

                user_.set_unusable_password()
                
                uassoc = FBAssociation(user=user_,  fbuid=user_data['uid'])
                uassoc.save()
                
                user_.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user_)
                email_feeds_form.save(user_)
                
                return HttpResponseRedirect('/')
        else:            
            form1 = forms.FBConnectRegisterForm(initial={
                'next': '/',
                'username': user_data['name'],
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
