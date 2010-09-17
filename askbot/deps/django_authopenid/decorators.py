import functools
from django.forms import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from askbot.deps.django_authopenid import forms
from askbot.utils.forms import get_next_url

def valid_password_login_provider_required(view_func):
    """decorator for a view function which will
    redirect to signin page with the next url parameter
    set unless request (either GET or POST has parameter
    'login_provider' and the provider uses password
    authentication method
    """
    @functools.wraps(view_func)
    def decorated_function(request):
        login_provider = request.REQUEST.get('login_provider', '').strip()
        try:
            forms.PasswordLoginProviderField().clean(login_provider)
            return view_func(request)
        except ValidationError:
            redirect_url = reverse('user_signin')
            next = get_next_url(request)
            if next:
                redirect_url += '?next=%s' % next
            return HttpResponseRedirect(redirect_url)
    return decorated_function
