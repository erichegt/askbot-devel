"""http-related utilities for askbot
"""
from copy import copy

def hide_passwords(data):
    """replaces content of values that may contain passsword
    with XXXXXX for better security"""
    if not data:
        return data

    #names of the fields are taken from forms
    #askbot.utils.forms.SetPasswordForm
    #askbat.deps.django_authopenid.forms.LoginForm
    #todo: forms need to be consolidated and names of the fields normalized
    fields = (
        'password',
        'password1',
        'password2',
        'new_password',
        'new_password_retyped'
    )

    for field in fields:
        if field in data:
            data[field] = 'XXXXXX'

    return data

def get_request_info(request):
    """return a reasonable string with the key contents of request object
    this function is intended for the use in logs and debugging
    all passwords will be obfuscated
    """
    info = 'path: %s\n' % request.get_full_path()
    info += 'method: %s\n' % request.method
    data = None
    if request.method == 'GET':
        data = request.GET
    elif request.method == 'POST':
        data = request.POST
    data = hide_passwords(copy(data))
    info += 'data: %s\n' % unicode(data)
    info += 'host: %s\n' % request.get_host()
    if request.user.is_authenticated():
        info += 'user ID: %d\n' % request.user.id
    else:
        info += 'user is anonymous\n'
    return info
