# -*- coding: utf-8 -*-
# Copyright (c) 2007, 2008, Benoît Chesneau
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


from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _
from django.conf import settings
from askbot.conf import settings as askbot_settings
import types
import re
from django.utils.safestring import mark_safe
from askbot.deps.recaptcha_django import ReCaptchaField
from askbot.utils.forms import NextUrlField, UserNameField, UserEmailField, SetPasswordForm
EXTERNAL_LOGIN_APP = settings.LOAD_EXTERNAL_LOGIN_APP()

# needed for some linux distributions like debian
try:
    from openid.yadis import xri
except ImportError:
    from yadis import xri
    
from askbot.utils.forms import clean_next
from askbot.deps.django_authopenid.models import ExternalLoginData

__all__ = ['OpenidSigninForm', 'ClassicLoginForm', 'OpenidVerifyForm',
        'OpenidRegisterForm', 'ClassicRegisterForm', 'ChangePasswordForm',
        'ChangeEmailForm', 'EmailPasswordForm', 'DeleteForm',
        'ChangeOpenidForm']

class OpenidSigninForm(forms.Form):
    """ signin form """
    openid_url = forms.CharField(max_length=255, widget=forms.widgets.TextInput(attrs={'class': 'openid-login-input', 'size':80}))
    next = NextUrlField()

    def clean_openid_url(self):
        """ test if openid is accepted """
        if 'openid_url' in self.cleaned_data:
            openid_url = self.cleaned_data['openid_url']
            if xri.identifierScheme(openid_url) == 'XRI' and getattr(
                settings, 'OPENID_DISALLOW_INAMES', False
                ):
                raise forms.ValidationError(_('i-names are not supported'))
            return self.cleaned_data['openid_url']

class ClassicLoginForm(forms.Form):
    """ legacy account signin form """
    next = NextUrlField()
    username = UserNameField(required=False,skip_clean=True)
    password = forms.CharField(max_length=128, 
            widget=forms.widgets.PasswordInput(attrs={'class':'required login'}), 
            required=False)

    def __init__(self, data=None, files=None, auto_id='id_%s',
            prefix=None, initial=None): 
        super(ClassicLoginForm, self).__init__(data, files, auto_id,
                prefix, initial)
        self.user_cache = None

    def _clean_nonempty_field(self,field):
        value = None
        if field in self.cleaned_data:
            value = str(self.cleaned_data[field]).strip()
            if value == '':
                value = None
        self.cleaned_data[field] = value
        return value 

    def clean_username(self):
        return self._clean_nonempty_field('username')

    def clean_password(self):
        return self._clean_nonempty_field('password')

    def clean(self):
        """ 
        this clean function actually cleans username and password

        test if password is valid for this username 
        this is really the "authenticate" function
        also openid_auth is not an authentication backend
        since it's written in a way that does not comply with
        the Django convention
        """

        error_list = []
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']

        self.user_cache = None
        if username and password: 
            if settings.USE_EXTERNAL_LEGACY_LOGIN == True:
                pw_ok = False
                try:
                    pw_ok = EXTERNAL_LOGIN_APP.api.check_password(username,password)
                except forms.ValidationError, e:
                    error_list.extend(e.messages)
                if pw_ok:
                    external_user = ExternalLoginData.objects.get(external_username=username)
                    if external_user.user == None:
                        return self.cleaned_data
                    user = external_user.user
                    openid_logins = user.userassociation_set.all()
                    
                    if len(openid_logins) > 0:
                        msg1 = _('Account with this name already exists on the forum')
                        msg2 = _('can\'t have two logins to the same account yet, sorry.')
                        error_list.append(msg1)
                        error_list.append(msg2)
                        self._errors['__all__'] = forms.util.ErrorList(error_list)
                        return self.cleaned_data
                    else:
                        #synchronize password with external login
                        user.set_password(password)
                        user.save()
                        #this auth will always succeed
                        self.user_cache = authenticate(username=user.username,\
                                                        password=password)
                else:
                    #keep self.user_cache == None
                    #nothing to do, error message will be set below
                    pass
            else:
                self.user_cache = authenticate(username=username, password=password)

            if self.user_cache is None:
                del self.cleaned_data['username']
                del self.cleaned_data['password']
                error_list.insert(0,(_("Please enter valid username and password "
                                    "(both are case-sensitive).")))
            elif self.user_cache.is_active == False:
                error_list.append(_("This account is inactive."))
            if len(error_list) > 0:
                error_list.insert(0,_('Login failed.'))
        elif password == None and username == None:
            error_list.append(_('Please enter username and password'))
        elif password == None:
            error_list.append(_('Please enter your password'))
        elif username == None:
            error_list.append(_('Please enter user name'))
        if len(error_list) > 0:
            self._errors['__all__'] = forms.util.ErrorList(error_list)
        return self.cleaned_data

    def get_user(self):
        """ get authenticated user """
        return self.user_cache
            

class OpenidRegisterForm(forms.Form):
    """ openid signin form """
    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()

class OpenidVerifyForm(forms.Form):
    """ openid verify form (associate an openid with an account) """
    next = NextUrlField()
    username = UserNameField(must_exist=True)
    password = forms.CharField(max_length=128, 
            widget=forms.widgets.PasswordInput(attrs={'class':'required login'}))
    
    def __init__(self, data=None, files=None, auto_id='id_%s',
            prefix=None, initial=None): 
        super(OpenidVerifyForm, self).__init__(data, files, auto_id,
                prefix, initial)
        self.user_cache = None

    def clean_password(self):
        """ test if password is valid for this user """
        if 'username' in self.cleaned_data and \
                'password' in self.cleaned_data:
            self.user_cache =  authenticate(
                    username = self.cleaned_data['username'], 
                    password = self.cleaned_data['password']
            )
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a valid \
                    username and password. Note that both fields are \
                    case-sensitive."))
            elif self.user_cache.is_active == False:
                raise forms.ValidationError(_("This account is inactive."))
            return self.cleaned_data['password']

    def get_user(self):
        """ get authenticated user """
        return self.user_cache

class ClassicRegisterForm(SetPasswordForm):
    """ legacy registration form """

    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()
    #fields password1 and password2 are inherited
    recaptcha = ReCaptchaField()

class ChangePasswordForm(SetPasswordForm):
    """ change password form """
    oldpw = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required'}),
                label=mark_safe(_('Current password')))

    def __init__(self, data=None, user=None, *args, **kwargs):
        if user is None:
            raise TypeError("Keyword argument 'user' must be supplied")
        super(ChangePasswordForm, self).__init__(data, *args, **kwargs)
        self.user = user

    def clean_oldpw(self):
        """ test old password """
        if not self.user.check_password(self.cleaned_data['oldpw']):
            raise forms.ValidationError(_("Old password is incorrect. \
                    Please enter the correct password."))
        return self.cleaned_data['oldpw']
        
class ChangeEmailForm(forms.Form):
    """ change email form """
    email = UserEmailField(skip_clean=True)

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, \
            initial=None, user=None):
        super(ChangeEmailForm, self).__init__(data, files, auto_id, 
                prefix, initial)
        self.user = user

    def clean_email(self):
        """ check if email don't exist """
        if 'email' in self.cleaned_data:
            if askbot_settings.EMAIL_UNIQUE == True:
                try:
                    user = User.objects.get(email = self.cleaned_data['email'])
                    if self.user and self.user == user:   
                        return self.cleaned_data['email']
                except User.DoesNotExist:
                    return self.cleaned_data['email']
                except User.MultipleObjectsReturned:
                    raise forms.ValidationError(u'There is already more than one \
                        account registered with that e-mail address. Please try \
                        another.')
                raise forms.ValidationError(u'This email is already registered \
                    in our database. Please choose another.')
            else:
                return self.cleaned_data['email']
        
class ChangeopenidForm(forms.Form):
    """ change openid form """
    openid_url = forms.CharField(max_length=255,
            widget=forms.TextInput(attrs={'class': "required" }))

    def __init__(self, data=None, user=None, *args, **kwargs):
        if user is None:
            raise TypeError("Keyword argument 'user' must be supplied")
        super(ChangeopenidForm, self).__init__(data, *args, **kwargs)
        self.user = user

class DeleteForm(forms.Form):
    """ confirm form to delete an account """
    confirm = forms.CharField(widget=forms.CheckboxInput(attrs={'class':'required'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'required'}))

    def __init__(self, data=None, files=None, auto_id='id_%s',
            prefix=None, initial=None, user=None):
        super(DeleteForm, self).__init__(data, files, auto_id, prefix, initial)
        self.test_openid = False
        self.user = user

    def clean_password(self):
        """ check if we have to test a legacy account or not """
        if 'password' in self.cleaned_data:
            if not self.user.check_password(self.cleaned_data['password']):
                self.test_openid = True
        return self.cleaned_data['password']


class EmailPasswordForm(forms.Form):
    """ send new password form """
    username = UserNameField(skip_clean=True,label=mark_safe(_('Your user name (<i>required</i>)')))

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None, 
            initial=None):
        super(EmailPasswordForm, self).__init__(data, files, auto_id, 
                prefix, initial)
        self.user_cache = None

    def clean_username(self):
        """ get user for this username """
        if 'username' in self.cleaned_data:
            try:
                self.user_cache = User.objects.get(
                        username = self.cleaned_data['username'])
            except:
                raise forms.ValidationError(_("Incorrect username."))
        return self.cleaned_data['username']
