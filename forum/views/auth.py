from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.http import urlquote_plus
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,  logout
from django.http import get_host
import types
import datetime

from forum.models import AuthKeyUserAssociation, ValidationHash
from forum.authentication.forms import SimpleRegistrationForm, SimpleEmailSubscribeForm, \
        TemporaryLoginRequestForm, ChangePasswordForm, SetPasswordForm
from forum.utils.email import send_email

from forum.authentication.base import InvalidAuthentication
from forum.authentication import AUTH_PROVIDERS

from forum.models import Question, Answer

def signin_page(request, action=None):
    if action is None:
        request.session['on_signin_url'] = request.META.get('HTTP_REFERER', '/')
    else:
        request.session['on_signin_action'] = action
        request.session['on_signin_url'] = reverse('auth_action_signin', kwargs={'action': action})

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
                    request.user.message_set.create(message=_('The new credentials are now associated with your account'))
                    return HttpResponseRedirect(reverse('user_authsettings'))

            return HttpResponseRedirect(reverse('auth_signin'))
        else:
            if isinstance(assoc_key, (type, User)):
                return login_and_forward(request, assoc_key) 

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
            user_ = User(username=form1.cleaned_data['username'], email=form1.cleaned_data['email'])
            user_.email_isvalid = request.session.get('auth_validated_email', '') == form1.cleaned_data['email']
            user_.set_unusable_password()

            user_.save()

            if not user_.email_isvalid:
                send_validation_email(user_)

            try:
                assoc_key = request.session['assoc_key']
                auth_provider = request.session['auth_provider']
            except:
                request.session['auth_error'] = _("Oops, something went wrong in the middle of this process. Please try again.")
                return HttpResponseRedirect(request.session.get('on_signin_url', reverse('auth_signin'))) 

            uassoc = AuthKeyUserAssociation(user=user_, key=request.session['assoc_key'], provider=request.session['auth_provider'])
            uassoc.save()

            email_feeds_form.save(user_)

            del request.session['assoc_key']
            del request.session['auth_provider']

            if user_.email_isvalid:
                return login_and_forward(request, user_)
            else:
                return HttpResponseRedirect(reverse('index'))
    else:
        provider_class = AUTH_PROVIDERS[request.session['auth_provider']].consumer
        user_data = provider_class.get_user_data(request.session['assoc_key'])

        username = user_data.get('username', '')
        email = user_data.get('email', '')

        if not email:
            email = request.session.get('auth_email_request', '')

        if email:
            request.session['auth_validated_email'] = email

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

def request_temp_login(request):
    if request.method == 'POST':
        form = TemporaryLoginRequestForm(request.POST)

        if form.is_valid():
            user = form.user_cache

            try:
                hash = get_object_or_404(ValidationHash, user=user, type='templogin')
                if hash.expiration < datetime.datetime.now():
                    hash.delete()
                    return request_temp_login(request)
            except:
                hash = ValidationHash.objects.create_new(user, 'templogin', [user.id])

            send_email(_("Temporary login link"), [user.email], "auth/temp_login_email.html", {
                'temp_login_code': hash,
                'user': user
            })

            request.user.message_set.create(message=_("An email has been sent with your temporary login key"))

            return HttpResponseRedirect(reverse('index'))
    else:
        form = TemporaryLoginRequestForm()

    return render_to_response(
            'auth/temp_login_request.html', {'form': form}, 
            context_instance=RequestContext(request))

def temp_signin(request, user, code):
    user = get_object_or_404(User, id=user)

    if (ValidationHash.objects.validate(code, user, 'templogin', [user.id])):
        return login_and_forward(request,  user, reverse('user_authsettings'),
                _("You are logged in with a temporary access key, please take the time to fix your issue with authentication."))
    else:
        raise Http404()

def send_validation_email(user):
    hash = ValidationHash.objects.create_new(user, 'email', [user.email])
    send_email(_("Email Validation"), [user.email], "auth/email_validation.html", {
        'validation_code': hash,
        'user': user
    })

def validate_email(request, user, code):
    user = get_object_or_404(User, id=user)

    if (ValidationHash.objects.validate(code, user, 'email', [user.email])):
        user.email_isvalid = True
        user.save()
        return login_and_forward(request,  user, None, _("Thank you, your email is now validated."))
    else:
        raise Http404()

@login_required
def auth_settings(request):
    """
    change password view.

    url : /changepw/
    template: authopenid/changepw.html
    """
    user_ = request.user
    auth_keys = user_.auth_keys.all()

    if user_.has_usable_password():
        FormClass = ChangePasswordForm
    else:
        FormClass = SetPasswordForm

    if request.POST:
        form = FormClass(request.POST, user=user_)
        if form.is_valid():
            if user_.has_usable_password():
                request.user.message_set.create(message=_("Your password was changed"))
            else:
                request.user.message_set.create(message=_("New password set"))
                form = ChangePasswordForm(user=user_)
                
            user_.set_password(form.cleaned_data['password1'])
            user_.save()
            return HttpResponseRedirect(reverse('user_authsettings'))
    else:
        form = FormClass(user=user_)

    auth_keys_list = []

    for k in auth_keys:
        provider = AUTH_PROVIDERS.get(k.provider, None)

        if provider is not None:
            name =  "%s: %s" % (provider.context.human_name, provider.context.readable_key(k))
        else:
            from forum.authentication.base import ConsumerTemplateContext
            "unknown: %s" % ConsumerTemplateContext.readable_key(k)

        auth_keys_list.append({
            'name': name,
            'id': k.id
        })

    return render_to_response('auth/auth_settings.html', {
        'form': form,
        'has_password': user_.has_usable_password(),
        'auth_keys': auth_keys_list,
    }, context_instance=RequestContext(request))

def remove_external_provider(request, id):
    association = get_object_or_404(AuthKeyUserAssociation, id=id)
    request.user.message_set.create(message=_("You removed the association with %s") % association.provider)
    association.delete()
    return HttpResponseRedirect(reverse('user_authsettings'))

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

def login_and_forward(request,  user, forward=None, message=None):
    old_session = request.session.session_key
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request,  user)

    from forum.models import user_logged_in
    user_logged_in.send(user=user,session_key=old_session,sender=None)

    if not forward:
        signin_action = request.session.get('on_signin_action', None)
        if not signin_action:
            forward = request.session.get('on_signin_url', None)

            if not forward:
                forward = reverse('index')
        else:
            try:
                forward = POST_SIGNIN_ACTIONS[signin_action](user)
            except:
                forward = reverse('index')

    if message is None:
        message = _("Welcome back %s, you are now logged in") % user.username

    request.user.message_set.create(message=message)
    return HttpResponseRedirect(forward)

@login_required
def signout(request):
    """
    signout from the website. Remove openid from session and kill it.

    url : /signout/"
    """

    logout(request)
    return HttpResponseRedirect(reverse('index'))