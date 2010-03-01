from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,  logout
from django.http import get_host
import types

from forum.models import AuthKeyUserAssociation
from forum.authentication.forms import SimpleRegistrationForm, SimpleEmailSubscribeForm

from forum.authentication.base import InvalidAuthentication
from forum.authentication import AUTH_PROVIDERS

from forum.models import Question, Answer

def signin_page(request, action=None):
    if action is None:
        request.session['on_signin_url'] = request.META.get('HTTP_REFERER', '/')
    else:
        request.session['on_signin_action'] = action

    all_providers = [provider.context for provider in AUTH_PROVIDERS.values()]

    sort = lambda c1, c2: c1.weight - c2.weight
    can_show = lambda c: not request.user.is_authenticated() or c.show_to_logged_in_user

    bigicon_providers = sorted([
        context for context in all_providers if context.mode == 'BIGICON' and can_show(context)
    ], sort)

    smallicon_providers = sorted([
        context for context in all_providers if context.mode == 'SMALLICON' and can_show(context)
    ], sort)

    stackitem_providers = sorted([
        context for context in all_providers if context.mode == 'STACK_ITEM' and can_show(context)
    ], sort)

    try:
        msg = request.session['auth_error']
        del request.session['auth_error']
    except:
        msg = None

    return render_to_response(
            'auth/signin.html',
            {
                'msg': msg,
                'all_providers': all_providers,
                'bigicon_providers': bigicon_providers,
                'stackitem_providers': stackitem_providers,
                'smallicon_providers': smallicon_providers,
            },
            RequestContext(request))

def prepare_provider_signin(request, provider):
    force_email_request = request.REQUEST.get('validate_email', 'yes') == 'yes'
    request.session['force_email_request'] = force_email_request
    
    if provider in AUTH_PROVIDERS:
        provider_class = AUTH_PROVIDERS[provider].consumer

        try:
            request_url = provider_class.prepare_authentication_request(request,
                    reverse('auth_provider_done', kwargs={'provider': provider}))

            return HttpResponseRedirect(request_url)
        except NotImplementedError, e:
            return process_provider_signin(request, provider)
        except InvalidAuthentication, e:
            request.session['auth_error'] = e.message

        return HttpResponseRedirect(reverse('auth_signin'))    


def process_provider_signin(request, provider):
    if provider in AUTH_PROVIDERS:
        provider_class = AUTH_PROVIDERS[provider].consumer

        try:
            assoc_key = provider_class.process_authentication_request(request)
        except InvalidAuthentication, e:
            request.session['auth_error'] = e.message
            return HttpResponseRedirect(reverse('auth_signin'))

        if request.user.is_authenticated():
            if isinstance(assoc_key, (type, User)):
                if request.user != assoc_key:
                    request.session['auth_error'] = _("Sorry, these login credentials belong to anoother user. Plese terminate your current session and try again.")
                else:
                    request.session['auth_error'] = _("You are already logged in with that user.")
            else:
                try:
                    assoc = AuthKeyUserAssociation.objects.get(key=assoc_key)
                    if assoc.user == request.user:
                        request.session['auth_error'] = _("These login credentials are already associated with your account.")
                    else:
                        request.session['auth_error'] = _("Sorry, these login credentials belong to anoother user. Plese terminate your current session and try again.")
                except:
                    uassoc = AuthKeyUserAssociation(user=request.user, key=assoc_key, provider=provider)
                    uassoc.save()
                    request.session['auth_error'] = _("These new credentials are now associated with your account.")                    
            return HttpResponseRedirect(reverse('auth_signin'))

        try:
            assoc = AuthKeyUserAssociation.objects.get(key=assoc_key)
            user_ = assoc.user
            return login_and_forward(request, user_)
        except:
            request.session['assoc_key'] = assoc_key
            request.session['auth_provider'] = provider
            return HttpResponseRedirect(reverse('auth_external_register'))

    return HttpResponseRedirect(reverse('auth_signin'))

def external_register(request):
    if request.method == 'POST' and 'bnewaccount' in request.POST:
        form1 = SimpleRegistrationForm(request.POST)
        email_feeds_form = SimpleEmailSubscribeForm(request.POST)

        if (form1.is_valid() and email_feeds_form.is_valid()):
            tmp_pwd = User.objects.make_random_password()
            user_ = User.objects.create_user(form1.cleaned_data['username'],
                     form1.cleaned_data['email'], tmp_pwd)

            user_.set_unusable_password()

            uassoc = AuthKeyUserAssociation(user=user_, key=request.session['assoc_key'], provider=request.session['auth_provider'])
            uassoc.save()

            email_feeds_form.save(user_)

            del request.session['assoc_key']
            del request.session['auth_provider']
            return login_and_forward(request, user_)
    else:
        provider_class = AUTH_PROVIDERS[request.session['auth_provider']].consumer
        user_data = provider_class.get_user_data(request.session['assoc_key'])

        username = user_data.get('username', '')
        email = user_data.get('email', '')

        if not email:
            email = request.session.get('auth_email_request', '')

        form1 = SimpleRegistrationForm(initial={
            'next': '/',
            'username': username,
            'email': email,
        })
        email_feeds_form = SimpleEmailSubscribeForm()

    provider_context = AUTH_PROVIDERS[request.session['auth_provider']].context

    return render_to_response('auth/complete.html', {
        'form1': form1,
        'email_feeds_form': email_feeds_form,
        'provider':mark_safe(provider_context.human_name),
        'login_type':provider_context.id,
        'gravatar_faq_url':reverse('faq') + '#gravatar',
    }, context_instance=RequestContext(request))

def newquestion_signin_action(user):
    question = Question.objects.filter(author=user).order_by('-added_at')[0]
    return question.get_absolute_url()

def newanswer_signin_action(user):
    answer = Answer.objects.filter(author=user).order_by('-added_at')[0]
    return answer.get_absolute_url()

POST_SIGNIN_ACTIONS = {
    'newquestion': newquestion_signin_action,
    'newanswer': newanswer_signin_action,
}

def login_and_forward(request,  user):
    old_session = request.session.session_key
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request,  user)

    from forum.models import user_logged_in
    user_logged_in.send(user=user,session_key=old_session,sender=None)

    redirect = request.session.get('on_signin_url', None)

    if not redirect:
        signin_action = request.session.get('on_signin_action', None)
        if not signin_action:
            redirect = reverse('index')
        else:
            try:
                redirect = POST_SIGNIN_ACTIONS[signin_action](user)
            except:
                redirect = reverse('index')

    return HttpResponseRedirect(redirect)

@login_required
def signout(request):
    """
    signout from the website. Remove openid from session and kill it.

    url : /signout/"
    """

    logout(request)
    return HttpResponseRedirect(reverse('index'))