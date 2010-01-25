#this file contains stub functions that can be extended to support
#connect legacy login with external site
#from django import forms
import time 
from models import User as MWUser
from models import Logging
from models import MW_TS
import api
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.http import HttpResponseRedirect
from forms import RegisterForm
from forum.forms import SimpleEmailSubscribeForm
from forum.models import Question
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.db import transaction
from django_authopenid.models import ExternalLoginData
from django_authopenid.views import not_authenticated
from django.template import loader
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
import hashlib
import random

#not a view, but uses request and templates
def send_welcome_email(request, wiki_user, django_user):
    random.seed()
    confirmation_token = '%032x' % random.getrandbits(128)
    wiki_user.user_email_token = hashlib.md5(confirmation_token).hexdigest()
    wiki_user.user_email_token_expires = time.strftime(MW_TS,(time.gmtime(time.time() + 7*24*60*60)))
    wiki_user.save()

    link = 'http://' + settings.EXTERNAL_LEGACY_LOGIN_HOST \
        + settings.MEDIAWIKI_INDEX_PHP_URL \
        + '?title=Special:Confirmemail/' \
        + confirmation_token

    pw_link = 'http://' + settings.EXTERNAL_LEGACY_LOGIN_HOST \
        + settings.MEDIAWIKI_INDEX_PHP_URL \
        + '?title=Password_recovery'

    if wiki_user.user_title == 'prof':
        template_name = 'mediawiki/welcome_professor_email.txt'
    else:
        template_name = 'mediawiki/welcome_email.txt'
    t = loader.get_template(template_name)

    data = {
            'email_confirmation_url':mark_safe(link),
            'admin_email':settings.DEFAULT_FROM_EMAIL,
            'first_name':wiki_user.user_first_name,
            'last_name':wiki_user.user_last_name,
            'login_name':wiki_user.user_name,
            'title':wiki_user.user_title,
            'user_email':wiki_user.user_email,
            'forum_screen_name':django_user.username,
            'password_recovery_url':mark_safe(pw_link),
            }
    body = t.render(RequestContext(request,data))
    if wiki_user.user_title in ('prof','dr'):
        subject = _('%(title)s %(last_name)s, welcome to the OSQA online community!') \
            % {'title':wiki_user.get_user_title_display(),'last_name':wiki_user.user_last_name }
    else:
        subject = _('%(first_name)s, welcome to the OSQA online community!') \
            % {'first_name':wiki_user.user_first_name}
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject,body,from_email,[wiki_user.user_email])

@transaction.commit_manually
def signup(request):
    #this view works through forum and mediawiki (using apache include virtual injection)
    if request.is_include_virtual and request.REQUEST.get('was_posted','false')=='true':
        POST_INCLUDE_VIRTUAL = True
        POST_DATA = request.GET
    else:
        POST_INCLUDE_VIRTUAL = False
        if request.method == 'POST':
            POST_DATA = request.POST
        else:
            POST_DATA = None

    if POST_DATA:
        form = RegisterForm(POST_DATA)
        if form.is_valid():
            data = form.cleaned_data
            login_name = data['login_name']
            password = data['password']
            first_name = data['first_name']
            last_name = data['last_name']
            screen_name = data['screen_name']
            user_title = data['user_title']
            email = data['email']
            next = data['next']

            #register mediawiki user
            user_real_name = u'%s %s' % (first_name,last_name)
            mwu = MWUser(
                           user_name=login_name,
                           user_first_name = first_name,
                           user_last_name = last_name,
                           user_title = user_title,
                           user_email = email,
                           user_real_name=user_real_name
                        )
            mwu.set_default_options()
            mwu.save()
            #password may need user id so reload it
            mwu = MWUser.objects.get(user_name = login_name)
            mwu.set_password_and_token(password)
            mwu.save()

            #create log message
            mwu_creation_log = Logging(
                                        log_type='newusers',
                                        log_action='create',
                                        log_timestamp=time.strftime(MW_TS),
                                        log_params=str(mwu.user_id),
                                        log_namespace=2,
                                        log_user=mwu,
                                        log_deleted=0,
                                        )
            mwu_creation_log.save()
            mwu_creation_log.show_in_recent_changes(ip=request.META['REMOTE_ADDR'])
            print 'creation log saved'

            #register local user
            User.objects.create_user(screen_name, email, password)
            u = authenticate(username=screen_name, password=password)
            login(request,u)
            u.mediawiki_user = mwu
            u.save()

            #save email feed settings
            subscribe = SimpleEmailSubscribeForm(POST_DATA)
            if subscribe.is_valid():
                subscribe.save(user=u)

            #save external login data
            eld = ExternalLoginData(external_username=login_name, user=u)
            eld.save()

            transaction.commit()#commit so that user becomes visible on the wiki side

            #check password through API and load MW HTTP header session data
            api.check_password(login_name,password)

            print 'wiki login worked'

            #create welcome message on the forum
            u.message_set.create(message=_('Welcome to the OSQA community!'))
            print 'about to send confirmation email'
            send_welcome_email(request, mwu, u)

            if POST_INCLUDE_VIRTUAL:
                questions = Question.objects.exclude(deleted=True, closed=True, answer_accepted=True)
                questions = questions.order_by('-last_activity_at')[:5]
                response = render_to_response('mediawiki/thanks_for_joining.html', \
                                            {
                                                'wiki_user':mwu,
                                                'user':u,
                                                'questions':questions,
                                            },
                                            context_instance = RequestContext(request))
                api.set_login_cookies(response, u)
                #call session middleware now to get the django login cookies
                from django.contrib.sessions.middleware import SessionMiddleware
                sm = SessionMiddleware()
                response = sm.process_response(request,response)
                cookies = response.cookies
                for c in cookies.values():
                    response.write(c.js_output())
            else:
                response = HttpResponseRedirect(next)
                api.set_login_cookies(response, u)

            #set cookies so that user is logged in in the wiki too
            transaction.commit()
            return response
    else:
        form = RegisterForm()

    transaction.commit()
    if request.is_include_virtual:
        template_name = 'mediawiki/mediawiki_signup_content.html'
    else:
        template_name = 'mediawiki/mediawiki_signup.html'
    return render_to_response(template_name,{'form':form},\
                            context_instance=RequestContext(request))
