# -*- coding: utf-8 -*-
# Copyright (c) 2007, 2008, Benoît Chesneau
# Copyright (c) 2007 Simon Willison, original work on django-openid
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#      * Redistributions of source code must retain the above copyright
#      * notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#      * notice, this list of conditions and the following disclaimer in the
#      * documentation and/or other materials provided with the
#      * distribution.  Neither the name of the <ORGANIZATION> nor the names
#      * of its contributors may be used to endorse or promote products
#      * derived from this software without specific prior written
#      * permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.http import HttpResponseRedirect, get_host, Http404, \
                         HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext, loader, Context
from django.conf import settings
from askbot.conf import settings as askbot_settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.http import urlquote_plus
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.views.defaults import server_error

from openid.consumer.consumer import Consumer, \
    SUCCESS, CANCEL, FAILURE, SETUP_NEEDED
from openid.consumer.discover import DiscoveryFailure
from openid.extensions import sreg
# needed for some linux distributions like debian
try:
    from openid.yadis import xri
except ImportError:
    from yadis import xri

import re
import urllib

from askbot import forms as askbot_forms
from askbot.deps.django_authopenid.util import OpenID, DjangoOpenIDStore, from_openid_response
from askbot.deps.django_authopenid.models import UserAssociation, UserPasswordQueue, ExternalLoginData
from askbot.deps.django_authopenid import forms
import logging
from askbot.utils.forms import get_next_url

EXTERNAL_LOGIN_APP = settings.LOAD_EXTERNAL_LOGIN_APP()

#todo: decouple from askbot
def login(request,user):
    from django.contrib.auth import login as _login
    from askbot.models import signals

    if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
        EXTERNAL_LOGIN_APP.api.login(request,user)

    if not hasattr(user, 'backend'):
        user.backend = "django.contrib.auth.backends.ModelBackend"

    #1) get old session key
    session_key = request.session.session_key
    #2) get old search state
    search_state = None
    if 'search_state' in request.session:
        search_state = request.session['search_state']

    #3) login and get new session key
    _login(request,user)
    #4) transfer search_state to new session if found
    if search_state:
        search_state.set_logged_in()
        request.session['search_state'] = search_state
    #5) send signal with old session key as argument
    logging.debug('logged in user %s with session key %s' % (user.username, session_key))
    #todo: move to auth app
    signals.user_logged_in.send(user=user,session_key=session_key,sender=None)

#todo: uncouple this from askbot
def logout(request):
    from django.contrib.auth import logout as _logout#for login I've added wrapper below - called login
    if 'search_state' in request.session:
        request.session['search_state'].set_logged_out()
        request.session.modified = True
    _logout(request)
    if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
        EXTERNAL_LOGIN_APP.api.logout(request)

def get_url_host(request):
    if request.is_secure():
        protocol = 'https'
    else:
        protocol = 'http'
    host = escape(get_host(request))
    return '%s://%s' % (protocol, host)

def get_full_url(request):
    return get_url_host(request) + request.get_full_path()

def ask_openid(
            request,
            openid_url,
            redirect_to,
            on_failure=None,
            sreg_request=None
        ):
    """ basic function to ask openid and return response """
    request.encoding = 'UTF-8'
    on_failure = on_failure or signin_failure
    
    trust_root = getattr(
        settings, 'OPENID_TRUST_ROOT', get_url_host(request) + '/'
    )
    if xri.identifierScheme(openid_url) == 'XRI' and getattr(
            settings, 'OPENID_DISALLOW_INAMES', False
    ):
        msg = _("i-names are not supported")
        logging.debug('openid failed because i-names are not supported')
        return on_failure(request, msg)
    consumer = Consumer(request.session, DjangoOpenIDStore())
    try:
        auth_request = consumer.begin(openid_url)
    except DiscoveryFailure:
        msg = _(u"OpenID %(openid_url)s is invalid" % {'openid_url':openid_url})
        logging.debug(msg)
        return on_failure(request, msg)

    logging.debug('openid seemed to work')
    if sreg_request:
        logging.debug('adding sreg_request - wtf it is?')
        auth_request.addExtension(sreg_request)
    redirect_url = auth_request.redirectURL(trust_root, redirect_to)
    logging.debug('redirecting to %s' % redirect_url)
    return HttpResponseRedirect(redirect_url)

def complete(request, on_success=None, on_failure=None, return_to=None):
    """ complete openid signin """
    on_success = on_success or default_on_success
    on_failure = on_failure or default_on_failure
    
    logging.debug('in askbot.deps.django_authopenid.complete')
    
    consumer = Consumer(request.session, DjangoOpenIDStore())
    # make sure params are encoded in utf8
    params = dict((k,smart_unicode(v)) for k, v in request.GET.items())
    openid_response = consumer.complete(params, return_to)
    
    if openid_response.status == SUCCESS:
        logging.debug('SUCCESS')
        return on_success(request, openid_response.identity_url,
                openid_response)
    elif openid_response.status == CANCEL:
        logging.debug('CANCEL')
        return on_failure(request, 'The request was canceled')
    elif openid_response.status == FAILURE:
        logging.debug('FAILURE')
        return on_failure(request, openid_response.message)
    elif openid_response.status == SETUP_NEEDED:
        logging.debug('SETUP NEEDED')
        return on_failure(request, 'Setup needed')
    else:
        logging.debug('BAD OPENID STATUS')
        assert False, "Bad openid status: %s" % openid_response.status

def default_on_success(request, identity_url, openid_response):
    """ default action on openid signin success """
    logging.debug('')
    request.session['openid'] = from_openid_response(openid_response)
    logging.debug('performing default action on openid success %s' % get_next_url(request))
    return HttpResponseRedirect(get_next_url(request))

def default_on_failure(request, message):
    """ default failure action on signin """
    logging.debug('default openid failure action')
    return render_to_response('openid_failure.html', {
        'message': message
    })


def not_authenticated(func):
    """ decorator that redirect user to next page if
    he is already logged."""
    def decorated(request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(get_next_url(request))
        return func(request, *args, **kwargs)
    return decorated

#@not_authenticated
def signin(
        request,
        newquestion = False,
        newanswer = False,
    ):
    """
    signin page. It manages the legacy authentification (user/password) 
    and openid authentification
    
    url: /signin/
    
    template : authopenid/signin.htm
    """
    logging.debug('in signin view')
    request.encoding = 'UTF-8'
    on_failure = signin_failure
    email_feeds_form = askbot_forms.SimpleEmailSubscribeForm()
    initial_data = {'next': get_next_url(request)}
    openid_login_form = forms.OpenidSigninForm(initial = initial_data)
    password_login_form = forms.ClassicLoginForm(initial = initial_data)

    if request.method == 'POST':
        #'blogin' - password login
        if 'blogin' in request.POST:
            logging.debug('processing classic login form submission')
            password_login_form = forms.ClassicLoginForm(request.POST)
            if password_login_form.is_valid():
                #have login and password and need to login through external website
                if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
                    username = password_login_form.cleaned_data['username']
                    password = password_login_form.cleaned_data['password']
                    next = password_login_form.cleaned_data['next']
                    if password_login_form.get_user() == None:
                        #need to create internal user
                        
                        #1) save login and password temporarily in session
                        request.session['external_username'] = username
                        request.session['external_password'] = password
                        
                        #2) try to extract user email and nickname from external service
                        email = EXTERNAL_LOGIN_APP.api.get_email(username,password)
                        screen_name = EXTERNAL_LOGIN_APP.api.get_screen_name(username,password)
                        
                        #3) see if username clashes with some existing user
                        #if so, we have to prompt the user to pick a different name
                        username_taken = User.is_username_taken(screen_name)
                        
                        email_feeds_form = askbot_forms.SimpleEmailSubscribeForm()
                        form_data = {'username':screen_name,'email':email,'next':next}
                        form = forms.OpenidRegisterForm(initial=form_data)
                        template_data = {'form1':form,'username':screen_name,\
                                        'email_feeds_form':email_feeds_form,\
                                        'provider':mark_safe(settings.EXTERNAL_LEGACY_LOGIN_PROVIDER_NAME),\
                                        'login_type':'legacy',\
                                        'gravatar_faq_url':reverse('faq') + '#gravatar',\
                                        'external_login_name_is_taken':username_taken}
                        return render_to_response('authopenid/complete.html',template_data,\
                                context_instance=RequestContext(request))
                    else:
                        #user existed, external password is ok
                        user = password_login_form.get_user()
                        login(request,user)
                        response = HttpResponseRedirect(get_next_url(request))
                        EXTERNAL_LOGIN_APP.api.set_login_cookies(response,user)
                        return response
                else:
                    #regular password authentication
                    user = password_login_form.get_user()
                    login(request, user)
                    return HttpResponseRedirect(get_next_url(request))
        
        elif 'bnewaccount' in request.POST:
            logging.debug('processing classic (login/password) create account form submission')
            #register externally logged in password user with a new local account
            if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
                form = forms.OpenidRegisterForm(request.POST) 
                email_feeds_form = askbot_forms.SimpleEmailSubscribeForm(request.POST)
                form1_is_valid = form.is_valid()
                form2_is_valid = email_feeds_form.is_valid()
                if form1_is_valid and form2_is_valid:
                    #create the user
                    username = form.cleaned_data['username']
                    password = request.session.get('external_password',None)
                    email = form.cleaned_data['email']
                    if password and username:
                        User.objects.create_user(username,email,password)
                        user = authenticate(username=username,password=password)
                        EXTERNAL_LOGIN_APP.api.connect_local_user_to_external_user(user,username,password)
                        external_username = request.session['external_username']
                        eld = ExternalLoginData.objects.get(external_username=external_username)
                        eld.user = user
                        eld.save()
                        login(request,user)
                        email_feeds_form.save(user)
                        del request.session['external_username']
                        del request.session['external_password']
                        response = HttpResponseRedirect(reverse('index'))
                        EXTERNAL_LOGIN_APP.api.set_login_cookies(response, user)
                        return response
                    else:
                        if password:
                            del request.session['external_username']
                        if username:
                            del request.session['external_password']
                        return HttpResponseServerError()
                else:
                    #register after authenticating with external login
                    #provider
                    username = request.POST.get('username',None)
                    provider = mark_safe(settings.EXTERNAL_LEGACY_LOGIN_PROVIDER_NAME)
                    username_taken = User.is_username_taken(username)
                    data = {'login_type':'legacy','form1':form,'username':username,\
                        'email_feeds_form':email_feeds_form,'provider':provider,\
                        'gravatar_faq_url':reverse('faq') + '#gravatar',\
                        'external_login_name_is_taken':username_taken}
                    return render_to_response('authopenid/complete.html',data,
                            context_instance=RequestContext(request))
            else:
                raise Http404
        
        elif 'bsignin' in request.POST or 'openid_username' in request.POST:
            logging.debug('processing signin with openid submission')
            openid_login_form = forms.OpenidSigninForm(request.POST)
            if openid_login_form.is_valid():
                logging.debug('OpenidSigninForm is valid')
                next = openid_login_form.cleaned_data['next']
                sreg_req = sreg.SRegRequest(optional=['nickname', 'email'])
                redirect_to = "%s%s?%s" % (
                        get_url_host(request),
                        reverse('user_complete_signin'), 
                        urllib.urlencode({'next':next})
                )
                return ask_openid(request, 
                        openid_login_form.cleaned_data['openid_url'], 
                        redirect_to, 
                        on_failure=signin_failure, 
                        sreg_request=sreg_req)
            else:
                logging.debug('OpenidSigninForm is NOT valid! -> redisplay login view')

    if request.method == 'GET' and request.user.is_authenticated():
        view_subtype = 'change_openid'
    else:
        view_subtype = 'default'

    return show_signin_view(
                        request,
                        password_login_form = password_login_form,
                        openid_login_form = openid_login_form,
                        view_subtype = view_subtype
                    )

def show_signin_view(
                request,
                password_login_form = None,
                openid_login_form = None,
                account_recovery_form = None,
                account_recovery_message = None,
                view_subtype = 'default'
            ):
    """url-less utility function that populates
    context of template 'authopenid/signin.html'
    and returns its rendered output
    """

    allowed_subtypes = ('default', 'add_openid', 'email_sent', 'change_openid')
    assert(view_subtype in allowed_subtypes) 

    initial_data = {'next': get_next_url(request)}

    if password_login_form is None:
        password_login_form = forms.ClassicLoginForm(initial = initial_data)
    if openid_login_form is None:
        openid_login_form = forms.OpenidSigninForm(initial = initial_data)
    if account_recovery_form is None:
        account_recovery_form = forms.AccountRecoveryForm()#initial = initial_data)

    #if request is GET
    if request.method == 'GET':
        logging.debug('request method was GET')

    #todo: this sthuff must be executed on some signal
    #because askbot should have nothing to do with the login app
    from askbot.models import AnonymousQuestion as AQ
    session_key = request.session.session_key
    logging.debug('retrieving anonymously posted question associated with session %s' % session_key)
    qlist = AQ.objects.filter(session_key=session_key).order_by('-added_at')
    if len(qlist) > 0:
        question = qlist[0]
    else:
        question = None

    from askbot.models import AnonymousAnswer as AA
    session_key = request.session.session_key
    logging.debug('retrieving posted answer associated with session %s' % session_key)
    alist = AA.objects.filter(session_key=session_key).order_by('-added_at')
    if len(alist) > 0:
        answer = alist[0]
    else:
        answer = None

    if view_subtype == 'default' or view_subtype == 'email_sent':
        page_title = _('Please click any of the icons below to sign in')
    elif view_subtype == 'change_openid':
        page_title = _('If you wish, please change your login method')
    elif view_subtype == 'add_openid':
        page_title = _('Please wait a second! Your account is recovered, but ...')
    
    logging.debug('showing signin view')
    return render_to_response('authopenid/signin.html', {
        'page_class': 'openid-signin',
        'view_subtype': view_subtype, #add_openid|default
        'page_title': page_title,
        'question':question,
        'answer':answer,
        'password_login_form': password_login_form,
        'openid_login_form': openid_login_form,
        'account_recovery_form': account_recovery_form,
        'openid_error_message':  request.REQUEST.get('msg',''),
        'account_recovery_message': account_recovery_message,
    }, context_instance=RequestContext(request))

def complete_signin(request):
    """ in case of complete signin with openid """
    logging.debug('')#blank log just for the trace
    return complete(request, signin_success, signin_failure,
            get_url_host(request) + reverse('user_complete_signin'))

def signin_success(request, identity_url, openid_response):
    """
    openid signin success.
    
    If the openid is already registered, the user is redirected to 
    url set par next or in settings with OPENID_REDIRECT_NEXT variable.
    If none of these urls are set user is redirectd to /.
    
    if openid isn't registered user is redirected to register page.
    """

    logging.debug('')
    openid_ = from_openid_response(openid_response) #create janrain OpenID object
    request.session['openid'] = openid_
    try:
        logging.debug('trying to get user associated with this openid...')
        rel = UserAssociation.objects.get(openid_url__exact = str(openid_))
        logging.debug('success')
        if request.user.is_authenticated() and rel.user != request.user:
            logging.critical(
                    'possible account theft attempt by %s,%d to %s %d' % \
                    (
                        request.user.username,
                        request.user.id,
                        rel.user.username,
                        rel.user.id
                    )
                )
            raise Http404
        else:
            logging.debug('success')
    except UserAssociation.DoesNotExist:
        if request.user.is_anonymous():
            logging.debug('failed --> try to register brand new user')
            # try to register this new user
            return register(request)
        else:
            #store openid association
            try:
                user_assoc = UserAssociation.objects.get(user = request.user)
                user_assoc.openid_url = str(openid_)
            except UserAssociation.DoesNotExist:
                user_assoc = UserAssociation(
                                        user = request.user,
                                        openid_url = openid_
                                    )
            user_assoc.save()
            message = _('New login method saved. Thanks!')
            request.user.message_set.create(message = message)
            #set "account recovered" message
            return HttpResponseRedirect(get_next_url(request))
    user_ = rel.user
    if user_.is_active:
        user_.backend = "django.contrib.auth.backends.ModelBackend"
        logging.debug('user is active --> attached django auth ModelBackend --> calling login')
        login(request, user_)
        logging.debug('success')
    else:
        logging.debug('user is inactive, do not log them in')
    logging.debug('redirecting to %s' % get_next_url(request))
    return HttpResponseRedirect(get_next_url(request))

def is_association_exist(openid_url):
    """ test if an openid is already in database """
    is_exist = True
    try:
        uassoc = UserAssociation.objects.get(openid_url__exact = openid_url)
    except UserAssociation.DoesNotExist:
        is_exist = False
    logging.debug(str(is_exist))
    return is_exist

@not_authenticated
def register(request):
    """
    register an openid.
    
    If user is already a member he can associate their openid with 
    their account.
    
    A new account could also be created and automaticaly associated
    to the openid.
    
    url : /complete/
    
    template : authopenid/complete.html
    """
    
    logging.debug('')
    openid_ = request.session.get('openid', None)
    next = get_next_url(request)
    if not openid_:
        logging.debug('oops, no openid in session --> go back to signin')
        return HttpResponseRedirect(reverse('user_signin') + '?next=%s' % next)
    
    nickname = openid_.sreg.get('nickname', '')
    email = openid_.sreg.get('email', '')
    openid_register_form = forms.OpenidRegisterForm(initial={
        'next': next,
        'username': nickname,
        'email': email,
    }) 
    openid_verify_form = forms.OpenidVerifyForm(initial={
        'next': next,
        'username': nickname,
    })
    email_feeds_form = askbot_forms.SimpleEmailSubscribeForm()
    
    user_ = None
    is_redirect = False
    logging.debug('request method is %s' % request.method)
    if request.method == 'POST':
        if 'bnewaccount' in request.POST.keys():
            logging.debug('trying to create new account associated with openid')
            openid_register_form = forms.OpenidRegisterForm(request.POST)
            email_feeds_form = askbot_forms.SimpleEmailSubscribeForm(request.POST)
            if not openid_register_form.is_valid():
                logging.debug('OpenidRegisterForm is INVALID')
            elif not email_feeds_form.is_valid():
                logging.debug('SimpleEmailSubscribeForm is INVALID')
            else:
                logging.debug('OpenidRegisterForm and SimpleEmailSubscribeForm are valid')
                next = openid_register_form.cleaned_data['next']
                is_redirect = True
                logging.debug('creatng new django user %s ...' % \
                                openid_register_form.cleaned_data['username'])
                tmp_pwd = User.objects.make_random_password()
                user_ = User.objects.create_user(openid_register_form.cleaned_data['username'],
                         openid_register_form.cleaned_data['email'], tmp_pwd)
                
                user_.set_unusable_password()
                # make association with openid
                logging.debug('creating new openid user association %s <--> %s' \
                            % (user_.username, str(openid_)))
                uassoc = UserAssociation(openid_url=str(openid_), user_id=user_.id)
                uassoc.save()
                
                # login 
                user_.backend = "django.contrib.auth.backends.ModelBackend"
                logging.debug('logging the user in')
                login(request, user_)
                logging.debug('saving email feed settings')
                email_feeds_form.save(user_)
        elif 'bverify' in request.POST.keys():
            logging.debug('processing OpenidVerify form')
            openid_verify_form = forms.OpenidVerifyForm(request.POST)
            if openid_verify_form.is_valid():
                logging.debug('form is valid')
                is_redirect = True
                next = openid_verify_form.cleaned_data['next']
                user_ = openid_verify_form.get_user()
                logging.debug('creating new openid user association %s <--> %s' \
                            % (user_.username, str(openid_)))
                uassoc = UserAssociation(openid_url=str(openid_),
                        user_id=user_.id)
                uassoc.save()
                logging.debug('logging the user in')
                login(request, user_)
        
        #check if we need to post a question that was added anonymously
        #this needs to be a function call becase this is also done
        #if user just logged in and did not need to create the new account
        
        if user_ != None:
            if askbot_settings.EMAIL_VALIDATION == True:
                logging.debug('sending email validation')
                send_new_email_key(user_,nomessage=True)
                output = validation_email_sent(request)
                set_email_validation_message(user_) #message set after generating view
                return output
            if user_.is_authenticated():
                logging.debug('success, send user to main page')
                return HttpResponseRedirect(reverse('index'))
            else:
                logging.debug('have really strange error')
                raise Exception('openid login failed')#should not ever get here
    
    openid_str = str(openid_)
    bits = openid_str.split('/')
    base_url = bits[2] #assume this is base url
    url_bits = base_url.split('.')
    provider_name = url_bits[-2].lower()
    
    providers = {'yahoo':'<font color="purple">Yahoo!</font>',
                'flickr':'<font color="#0063dc">flick</font><font color="#ff0084">r</font>&trade;',
                'google':'Google&trade;',
                'aol':'<font color="#31658e">AOL</font>',
                'myopenid':'MyOpenID',
                }
    if provider_name not in providers:
        provider_logo = provider_name
        logging.error('openid provider named "%s" has no pretty customized logo' % provider_name)
    else:
        provider_logo = providers[provider_name]
    
    logging.debug('printing authopenid/complete.html output')
    return render_to_response('authopenid/complete.html', {
        'openid_register_form': openid_register_form,
        'openid_verify_form': openid_verify_form,
        'email_feeds_form': email_feeds_form,
        'provider':mark_safe(provider_logo),
        'username': nickname,
        'email': email,
        'login_type':'openid',
        'gravatar_faq_url':reverse('faq') + '#gravatar',
    }, context_instance=RequestContext(request))

def signin_failure(request, message):
    """
    falure with openid signin. Go back to signin page.

    template : "authopenid/signin.html"
    """
    logging.debug('')
    next = get_next_url(request)
    openid_login_form = forms.OpenidSigninForm(initial={'next': next})
    password_login_form = forms.ClassicLoginForm(initial={'next': next})
    
    return render_to_response('authopenid/signin.html', {
        'msg': message,
        'password_login_form': password_login_form,
        'openid_login_form': openid_login_form,
    }, context_instance=RequestContext(request))

@not_authenticated
def signup(request):
    """
    signup page. Create a legacy account
    
    url : /signup/"
    
    templates: authopenid/signup.html, authopenid/confirm_email.txt
    """
    logging.debug('')
    if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
        logging.debug('handling external legacy login registration')
        return HttpResponseRedirect(reverse('user_external_legacy_login_signup'))
    next = get_next_url(request)
    logging.debug('request method was %s' % request.method)
    if request.method == 'POST':
        form = forms.ClassicRegisterForm(request.POST)
        email_feeds_form = askbot_forms.SimpleEmailSubscribeForm(request.POST)
        
        #validation outside if to remember form values
        logging.debug('validating classic register form')
        form1_is_valid = form.is_valid()
        logging.debug('classic register form validated')
        form2_is_valid = email_feeds_form.is_valid()
        logging.debug('email feeds form validated')
        if form1_is_valid and form2_is_valid:
            logging.debug('both forms are valid')
            next = form.cleaned_data['next']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data['email']
            
            user_ = User.objects.create_user( username,email,password )
            logging.debug('new user %s created' % username)
            if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
                EXTERNAL_LOGIN_APP.api.create_user(username,email,password)
            
            user_.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user_)
            logging.debug('new user logged in')
            email_feeds_form.save(user_)
            logging.debug('email feeds form saved')
            
            # send email
            subject = _("Welcome email subject line")
            message_template = loader.get_template(
                    'authopenid/confirm_email.txt'
            )
            message_context = Context({ 
                'signup_url': askbot_settings.APP_URL + reverse('user_signin'),
                'username': username,
                'password': password,
            })
            message = message_template.render(message_context)
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                    [user_.email])
            logging.debug('new user with login and password created, confirmation email sent!')
            return HttpResponseRedirect(next)
        else:
            logging.debug('create classic account forms were invalid')
    else:
        form = forms.ClassicRegisterForm(initial={'next':next})
        email_feeds_form = askbot_forms.SimpleEmailSubscribeForm()
    logging.debug('printing legacy signup form')
    return render_to_response('authopenid/signup.html', {
        'form': form, 
        'email_feeds_form': email_feeds_form 
        }, context_instance=RequestContext(request))
    #what if request is not posted?

@login_required
def signout(request):
    """
    signout from the website. Remove openid from session and kill it.

    url : /signout/"
    """
    logging.debug('')
    try:
        logging.debug('deleting openid session var')
        del request.session['openid']
    except KeyError:
        logging.debug('failed')
        pass
    logout(request)
    logging.debug('user logged out')
    return HttpResponseRedirect(get_next_url(request))
    
def xrdf(request):
    url_host = get_url_host(request)
    logging.debug('what does this do??')
    return_to = [
        "%s%s" % (url_host, reverse('user_complete_signin'))
    ]
    return render_to_response('authopenid/yadis.xrdf', { 
        'return_to': return_to 
        }, context_instance=RequestContext(request))

@login_required
def account_settings(request):
    """
    index pages to changes some basic account settings :
     - change password
     - change email
     - associate a new openid
     - delete account

    url : /

    template : authopenid/settings.html
    """
    logging.debug('')
    msg = request.GET.get('msg', '')
    is_openid = True

    try:
        uassoc = UserAssociation.objects.get(
                user__username__exact=request.user.username
        )
    except:
        is_openid = False


    return render_to_response('authopenid/settings.html', {
        'msg': msg,
        'is_openid': is_openid
        }, context_instance=RequestContext(request))

@login_required
def changepw(request):
    """
    change password view.

    url : /changepw/
    template: authopenid/changepw.html
    """
    logging.debug('')
    user_ = request.user

    if user_.has_usable_password():
        if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
            return HttpResponseRedirect(reverse('user_external_legacy_login_issues'))
    else:
        raise Http404
    
    if request.POST:
        form = forms.ChangePasswordForm(request.POST, user=user_)
        if form.is_valid():
            user_.set_password(form.cleaned_data['password1'])
            user_.save()
            msg = _("Password changed.") 
            redirect = "%s?msg=%s" % (
                    reverse('user_account_settings'),
                    urlquote_plus(msg))
            return HttpResponseRedirect(redirect)
    else:
        form = forms.ChangePasswordForm(user=user_)

    return render_to_response('authopenid/changepw.html', {'form': form },
                                context_instance=RequestContext(request))

def find_email_validation_messages(user):
    msg_text = _('your email needs to be validated see %(details_url)s') \
        % {'details_url':reverse('faq') + '#validate'}
    return user.message_set.filter(message__exact=msg_text)

def set_email_validation_message(user):
    messages = find_email_validation_messages(user)
    msg_text = _('your email needs to be validated see %(details_url)s') \
        % {'details_url':reverse('faq') + '#validate'}
    if len(messages) == 0:
        user.message_set.create(message=msg_text)

def clear_email_validation_message(user):
    messages = find_email_validation_messages(user)
    messages.delete()

def set_new_email(user, new_email, nomessage=False):
    if new_email != user.email:
        user.email = new_email
        user.email_isvalid = False
        user.save()
        if askbot_settings.EMAIL_VALIDATION == True:
            send_new_email_key(user,nomessage=nomessage)

def _send_email_key(user):
    """private function. sends email containing validation key
    to user's email address
    """
    subject = _("Email verification subject line")
    message_template = loader.get_template('authopenid/email_validation.txt')
    import settings
    message_context = Context({
    'validation_link': askbot_settings.APP_URL + reverse(
                                                    'user_account_recover',
                                                    kwargs={'key':user.email_key}
                                                )
    })
    message = message_template.render(message_context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_new_email_key(user,nomessage=False):
    import random
    random.seed()
    user.email_key = '%032x' % random.getrandbits(128) 
    user.save()
    _send_email_key(user)
    if nomessage==False:
        set_email_validation_message(user)

@login_required
def send_email_key(request):
    """
    url = /email/sendkey/

    view that is shown right after sending email key
    email sending is called internally

    raises 404 if email validation is off
    if current email is valid shows 'key_not_sent' view of 
    authopenid/changeemail.html template
    """

    if askbot_settings.EMAIL_VALIDATION == True:
        if request.user.email_isvalid:
            return render_to_response('authopenid/changeemail.html',
                            { 'email': request.user.email, 
                              'action_type': 'key_not_sent', 
                              'change_link': reverse('user_changeemail')},
                              context_instance=RequestContext(request)
                              )
        else:
            send_new_email_key(request.user)
            return validation_email_sent(request)
    else:
        raise Http404

def account_recover(request, key = None):
    """view similar to send_email_key, except
    it allows user to recover an account by entering
    his/her email address

    this view will both - send the recover link and
    process it

    url name 'user_account_recover'
    """
    if request.method == 'POST':
        form = forms.AccountRecoveryForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email = email)
                send_new_email_key(user, nomessage = True)
                message = _(
                        'Please check your email and visit the enclosed link.'
                    )
                return show_signin_view(
                                request,
                                account_recovery_message = message,
                                view_subtype = 'email_sent'
                            )
            except User.DoesNotExist:
                message = _(
                        'Sorry we cound not find this email it our database. '
                        'If you think that this is an error - please contact '
                        'the site administrator'
                    )
                return show_signin_view(
                                request,
                                account_recovery_message = message,
                                account_recovery_form = form
                            )
        else:
            message = _('Please enter a valid email address')
            return show_signin_view(
                            request,
                            account_recovery_message = message,
                            account_recovery_form = form
                        )
    else:
        if key is None:
            raise Http404
        try:
            user = User.objects.get(email_key = key)
            user.email_key = None #delete the key so that nobody could use it again
            #todo: add email_key_timestamp field
            #and check key age
            login(request, user)
            return show_signin_view(request, view_subtype = 'add_openid')

        except User.DoesNotExist:
            message = _('Sorry this account recovery key has '
                    'expired or is invalid, please request a new one'
                    )
            return show_signin_view(
                            request,
                            account_recovery_message = message,
                        )
   

#internal server view used as return value by other views
def validation_email_sent(request):
    logging.debug('')
    return render_to_response('authopenid/changeemail.html',
                    { 'email': request.user.email, 
                    'change_email_url': reverse('user_changeemail'),
                    'action_type': 'validate', }, 
                     context_instance=RequestContext(request))

def verifyemail(request,id=None,key=None):
    """
    view that is shown when user clicks email validation link
    url = /email/verify/{{user.id}}/{{user.email_key}}/
    """
    logging.debug('')
    if askbot.settings.EMAIL_VALIDATION == True:
        user = User.objects.get(id=id)
        if user:
            if user.email_key == key:
                user.email_isvalid = True
                clear_email_validation_message(user)
                user.save()
                return render_to_response('authopenid/changeemail.html', {
                    'action_type': 'validation_complete',
                    }, context_instance=RequestContext(request))
            else:
                logging.error('hmm, no user found for email validation message - foul play?')
    raise Http404

@login_required
def changeemail(request, action='change'):
    """ 
    changeemail view. requires openid with request type GET

    url: /email/*

    template : authopenid/changeemail.html
    """
    logging.debug('')
    msg = request.GET.get('msg', None)
    extension_args = {}
    user_ = request.user

    if request.POST:
        if 'cancel' in request.POST:
            msg = _('your email was not changed')
            request.user.message_set.create(message=msg)
            return HttpResponseRedirect(get_next_url(request))
        form = forms.ChangeEmailForm(request.POST, user=user_)
        if form.is_valid():
            new_email = form.cleaned_data['email']
            if new_email != user_.email:
                if askbot_settings.EMAIL_VALIDATION == True:
                    action = 'validate'
                else:
                    action = 'done_novalidate'
                set_new_email(user_, new_email,nomessage=True)
            else:
                action = 'keep'

    elif not request.POST and 'openid.mode' in request.GET:
        redirect_to = get_url_host(request) + reverse('user_changeemail')
        return complete(request, emailopenid_success, 
                emailopenid_failure, redirect_to) 
    else:
        form = forms.ChangeEmailForm(initial={'email': user_.email},
                user=user_)
    
    output = render_to_response('authopenid/changeemail.html', {
        'form': form,
        'email': user_.email,
        'action_type': action,
        'gravatar_faq_url': reverse('faq') + '#gravatar',
        'change_email_url': reverse('user_changeemail'),
        'msg': msg 
        }, context_instance=RequestContext(request))

    if action == 'validate':
        set_email_validation_message(user_)

    return output

def emailopenid_success(request, identity_url, openid_response):
    logging.debug('')
    openid_ = from_openid_response(openid_response)

    user_ = request.user
    try:
        uassoc = UserAssociation.objects.get(
                openid_url__exact=identity_url
        )
    except:
        return emailopenid_failure(request, 
                _("No OpenID %s found associated in our database" % identity_url))

    if uassoc.user.username != request.user.username:
        return emailopenid_failure(request, 
                _("The OpenID %s isn't associated to current user logged in" % 
                    identity_url))
    
    new_email = request.session.get('new_email', '')
    if new_email:
        user_.email = new_email
        user_.save()
        del request.session['new_email']
    msg = _("Email Changed.")

    redirect = "%s?msg=%s" % (reverse('user_account_settings'),
            urlquote_plus(msg))
    return HttpResponseRedirect(redirect)
    

def emailopenid_failure(request, message):
    logging.debug('')
    redirect_to = "%s?msg=%s" % (
            reverse('user_changeemail'), urlquote_plus(message))
    return HttpResponseRedirect(redirect_to)
 
@login_required
def changeopenid(request):
    """
    change openid view. Allow user to change openid 
    associated to its username.

    url : /changeopenid/

    template: authopenid/changeopenid.html
    """
    logging.error('change openid view - never tested it yet!!!')

    extension_args = {}
    openid_url = ''
    has_openid = True
    msg = request.GET.get('msg', '')
        
    user_ = request.user

    try:
        uopenid = UserAssociation.objects.get(user=user_)
        openid_url = uopenid.openid_url
    except:
        has_openid = False
    
    redirect_to = get_url_host(request) + reverse('user_changeopenid')
    if request.POST and has_openid:
        form = forms.ChangeopenidForm(request.POST, user=user_)
        if form.is_valid():
            return ask_openid(request, form.cleaned_data['openid_url'],
                    redirect_to, on_failure=changeopenid_failure)
    elif not request.POST and has_openid:
        if 'openid.mode' in request.GET:
            return complete(request, changeopenid_success,
                    changeopenid_failure, redirect_to)    

    form = forms.ChangeopenidForm(initial={'openid_url': openid_url }, user=user_)
    return render_to_response('authopenid/changeopenid.html', {
        'form': form,
        'has_openid': has_openid, 
        'msg': msg 
        }, context_instance=RequestContext(request))

def changeopenid_success(request, identity_url, openid_response):
    logging.error('never tested this worflow')
    openid_ = from_openid_response(openid_response)
    is_exist = True
    try:
        uassoc = UserAssociation.objects.get(openid_url__exact=identity_url)
    except:
        is_exist = False
        
    if not is_exist:
        try:
            uassoc = UserAssociation.objects.get(
                    user__username__exact=request.user.username
            )
            uassoc.openid_url = identity_url
            uassoc.save()
        except:
            uassoc = UserAssociation(user=request.user, 
                    openid_url=identity_url)
            uassoc.save()
    elif uassoc.user.username != request.user.username:
        return changeopenid_failure(request, 
                _('This OpenID is already associated with another account.'))

    request.session['openids'] = []
    request.session['openids'].append(openid_)

    msg = _("OpenID %s is now associated with your account." % identity_url) 
    redirect = "%s?msg=%s" % (
            reverse('user_account_settings'), 
            urlquote_plus(msg))
    return HttpResponseRedirect(redirect)
    

def changeopenid_failure(request, message):
    logging.error('never tested this workflow')
    redirect_to = "%s?msg=%s" % (
            reverse('user_changeopenid'), 
            urlquote_plus(message))
    return HttpResponseRedirect(redirect_to)
  
@login_required
def delete(request):
    """
    delete view. Allow user to delete its account. Password/openid are required to 
    confirm it. He should also check the confirm checkbox.
    
    url : /delete
    
    template : authopenid/delete.html
    """
    logging.error('deleting account - never tested this')
    
    extension_args = {}
    
    user_ = request.user
    
    redirect_to = get_url_host(request) + reverse('user_delete') 
    if request.POST:
        form = forms.DeleteForm(request.POST, user=user_)
        if form.is_valid():
            if not form.test_openid:
                user_.delete() 
                return signout(request)
            else:
                return ask_openid(request, form.cleaned_data['password'],
                        redirect_to, on_failure=deleteopenid_failure)
    elif not request.POST and 'openid.mode' in request.GET:
        return complete(request, deleteopenid_success, deleteopenid_failure,
                redirect_to) 
    
    form = forms.DeleteForm(user=user_)
    
    msg = request.GET.get('msg','')
    return render_to_response('authopenid/delete.html', {
        'form': form, 
        'msg': msg, 
        }, context_instance=RequestContext(request))

def deleteopenid_success(request, identity_url, openid_response):
    logging.error('never tested this')
    openid_ = from_openid_response(openid_response)

    user_ = request.user
    try:
        uassoc = UserAssociation.objects.get(
                openid_url__exact=identity_url
        )
    except:
        return deleteopenid_failure(request,
                _("No OpenID %s found associated in our database" % identity_url))

    if uassoc.user.username == user_.username:
        user_.delete()
        return signout(request)
    else:
        return deleteopenid_failure(request,
                _("The OpenID %s isn't associated to current user logged in" % 
                    identity_url))
    
    msg = _("Account deleted.") 
    redirect = reverse('index') + u"/?msg=%s" % (urlquote_plus(msg))
    return HttpResponseRedirect(redirect)
    

def deleteopenid_failure(request, message):
    logging.error('never tested this')
    redirect_to = "%s?msg=%s" % (reverse('user_delete'), urlquote_plus(message))
    return HttpResponseRedirect(redirect_to)

def external_legacy_login_info(request):
    logging.debug('maybe this view does not belong in this library')
    feedback_url = reverse('feedback')
    return render_to_response('authopenid/external_legacy_login_info.html', 
                    {'feedback_url':feedback_url}, 
                    context_instance=RequestContext(request))

def sendpw(request):
    """
    send a new password to the user. It return a mail with 
    a new pasword and a confirm link in. To activate the 
    new password, the user should click on confirm link.
    
    url : /sendpw/
    
    templates :  authopenid/sendpw_email.txt, authopenid/sendpw.html
    """
    logging.debug('')
    if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
        logging.debug('delegating to view dealing with external password recovery')
        return HttpResponseRedirect(reverse('user_external_legacy_login_issues'))
    
    msg = request.GET.get('msg','')
    logging.debug('request method is %s' % request.method)
    if request.method == 'POST':
        form = forms.EmailPasswordForm(request.POST)
        if form.is_valid():
            logging.debug('EmailPasswordForm is valid')
            new_pw = User.objects.make_random_password()
            confirm_key = UserPasswordQueue.objects.get_new_confirm_key()
            try:
                uqueue = UserPasswordQueue.objects.get(
                        user=form.user_cache
                )
            except:
                uqueue = UserPasswordQueue(
                        user=form.user_cache
                )
            uqueue.new_password = new_pw
            uqueue.confirm_key = confirm_key
            uqueue.save()
            # send email 
            subject = _("Request for new password")
            message_template = loader.get_template(
                    'authopenid/sendpw_email.txt')
            key_link = askbot_settings.APP_URL + reverse('user_confirmchangepw') + '?key=' + confirm_key
            logging.debug('emailing new password for %s' % form.user_cache.username)
            message_context = Context({ 
                'site_url': askbot_settings.APP_URL + reverse('index'),
                'key_link': key_link,
                'username': form.user_cache.username,
                'password': new_pw,
            })
            message = message_template.render(message_context)
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                    [form.user_cache.email])
            msg = _("A new password and the activation link were sent to your email address.")
    else:
        form = forms.EmailPasswordForm()
    
    logging.debug('showing reset password form')
    return render_to_response('authopenid/sendpw.html', {
        'form': form,
        'msg': msg 
        }, context_instance=RequestContext(request))

def confirmchangepw(request):
    """
    view to set new password when the user click on confirm link
    in its mail. Basically it check if the confirm key exist, then
    replace old password with new password and remove confirm
    ley from the queue. Then it redirect the user to signin
    page.
    
    url : /sendpw/confirm/?key
    
    """
    logging.debug('')
    confirm_key = request.GET.get('key', '')
    if not confirm_key:
        logging.error('someone called confirm password without a key!')
        return HttpResponseRedirect(reverse('index'))
    
    try:
        uqueue = UserPasswordQueue.objects.get(
                confirm_key__exact=confirm_key
        )
    except:
        msg = _("Could not change password. Confirmation key '%s'\
                is not registered." % confirm_key) 
        logging.error(msg)
        redirect = "%s?msg=%s" % (
                reverse('user_sendpw'), urlquote_plus(msg))
        return HttpResponseRedirect(redirect)
    
    try:
        user_ = User.objects.get(id=uqueue.user.id)
    except:
        msg = _("Can not change password. User don't exist anymore \
                in our database.") 
        logging.error(msg)
        redirect = "%s?msg=%s" % (reverse('user_sendpw'), 
                urlquote_plus(msg))
        return HttpResponseRedirect(redirect)
    
    user_.set_password(uqueue.new_password)
    user_.save()
    uqueue.delete()
    msg = _("Password changed for %s. You may now sign in." % 
            user_.username) 
    logging.debug(msg)
    redirect = "%s?msg=%s" % (reverse('user_signin'), 
                                        urlquote_plus(msg))
    
    return HttpResponseRedirect(redirect)
