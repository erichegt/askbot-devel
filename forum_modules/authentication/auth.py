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
                FormClass = ChangePasswordForm
                
            user_.set_password(form.cleaned_data['password1'])
            user_.save()
            return HttpResponseRedirect(reverse('user_authsettings'))
    
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
