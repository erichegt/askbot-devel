from django import forms
import re
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.conf import settings
from django.http import str_to_unicode
from django.contrib.auth.models import User
import urllib

DEFAULT_NEXT = '/' + getattr(settings, 'FORUM_SCRIPT_ALIAS')
def clean_next(next):
    if next is None:
        return DEFAULT_NEXT
    next = str_to_unicode(urllib.unquote(next), 'utf-8')
    next = next.strip()
    if next.startswith('/'):
        return next
    return DEFAULT_NEXT

def get_next_url(request):
    return clean_next(request.REQUEST.get('next'))

class StrippedNonEmptyCharField(forms.CharField):
    def clean(self,value):
        value = value.strip()
        if self.required and value == '':
            raise forms.ValidationError(_('this field is required'))
        return value

class NextUrlField(forms.CharField):
    def __init__(self):
        super(NextUrlField,self).__init__(max_length = 255,widget = forms.HiddenInput(),required = False)
    def clean(self,value):
        return clean_next(value)

login_form_widget_attrs = { 'class': 'required login' }
username_re = re.compile(r'^[\w ]+$')

class UserNameField(StrippedNonEmptyCharField):
    RESERVED_NAMES = (u'fuck', u'shit', u'ass', u'sex', u'add',
                       u'edit', u'save', u'delete', u'manage', u'update', 'remove', 'new')
    def __init__(self,db_model=User, db_field='username', must_exist=False,skip_clean=False,label=_('choose a username'),**kw):
        self.must_exist = must_exist
        self.skip_clean = skip_clean
        self.db_model = db_model 
        self.db_field = db_field
        error_messages={'required':_('user name is required'),
                        'taken':_('sorry, this name is taken, please choose another'),
                        'forbidden':_('sorry, this name is not allowed, please choose another'),
                        'missing':_('sorry, there is no user with this name'),
                        'multiple-taken':_('sorry, we have a serious error - user name is taken by several users'),
                        'invalid':_('user name can only consist of letters, empty space and underscore'),
                    }
        if 'error_messages' in kw:
            error_messages.update(kw['error_messages'])
            del kw['error_messages']
        super(UserNameField,self).__init__(max_length=30,
                widget=forms.TextInput(attrs=login_form_widget_attrs),
                label=label,
                error_messages=error_messages,
                **kw
                )

    def clean(self,username):
        """ validate username """
        if self.skip_clean == True:
            return username
        if hasattr(self, 'user_instance') and isinstance(self.user_instance, User):
            if username == self.user_instance.username:
                return username
        try:
            username = super(UserNameField, self).clean(username)
        except forms.ValidationError:
            raise forms.ValidationError(self.error_messages['required'])
        if self.required and not username_re.search(username):
            raise forms.ValidationError(self.error_messages['invalid'])
        if username in self.RESERVED_NAMES:
            raise forms.ValidationError(self.error_messages['forbidden'])
        try:
            user = self.db_model.objects.get(
                    **{'%s' % self.db_field : username}
            )
            if user:
                if self.must_exist:
                    return username
                else:
                    raise forms.ValidationError(self.error_messages['taken'])
        except self.db_model.DoesNotExist:
            if self.must_exist:
                raise forms.ValidationError(self.error_messages['missing'])
            else:
                return username
        except self.db_model.MultipleObjectsReturned:
            raise forms.ValidationError(self.error_messages['multiple-taken'])

class UserEmailField(forms.EmailField):
    def __init__(self,skip_clean=False,**kw):
        self.skip_clean = skip_clean
        super(UserEmailField,self).__init__(widget=forms.TextInput(attrs=dict(login_form_widget_attrs,
            maxlength=200)), label=mark_safe(_('your email address')),
            error_messages={'required':_('email address is required'),
                            'invalid':_('please enter a valid email address'),
                            'taken':_('this email is already used by someone else, please choose another'),
                            },
            **kw
            )

    def clean(self,email):
        """ validate if email exist in database
        from legacy register
        return: raise error if it exist """
        email = super(UserEmailField,self).clean(email.strip())
        if self.skip_clean:
            return email
        if settings.EMAIL_UNIQUE == True:
            try:
                user = User.objects.get(email = email)
                raise forms.ValidationError(self.error_messsages['taken'])
            except User.DoesNotExist:
                return email
            except User.MultipleObjectsReturned:
                raise forms.ValidationError(self.error_messages['taken'])
        else:
            return email 

class SetPasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=login_form_widget_attrs),
                                label=_('choose password'),
                                error_messages={'required':_('password is required')},
                                )
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=login_form_widget_attrs),
                                label=mark_safe(_('retype password')),
                                error_messages={'required':_('please, retype your password'),
                                                'nomatch':_('sorry, entered passwords did not match, please try again')},
                                )
    def clean_password2(self):
        """
        Validates that the two password inputs match.
        
        """
        if 'password1' in self.cleaned_data:
            if self.cleaned_data['password1'] == self.cleaned_data['password2']:
                self.password = self.cleaned_data['password2']
                self.cleaned_data['password'] = self.cleaned_data['password2']
                return self.cleaned_data['password2']
            else:
                del self.cleaned_data['password2']
                raise forms.ValidationError(self.fields['password2'].error_messages['nomatch'])
        else:
            return self.cleaned_data['password2']

