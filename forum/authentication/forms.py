from forum.utils.forms import NextUrlField,  UserNameField,  UserEmailField, SetPasswordForm
from forum.models import EmailFeedSetting, Question, User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django import forms
from forum.forms import EditUserEmailFeedsForm
import logging

class SimpleRegistrationForm(forms.Form):
    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()

class TemporaryLoginRequestForm(forms.Form):
    def __init__(self, data=None):
        super(TemporaryLoginRequestForm, self).__init__(data)
        self.user_cache = None

    email = forms.EmailField(
            required=True,
            label=_("Your account email"),
            error_messages={
                'required': _("You cannot leave this field blank"),
                'invalid': _('please enter a valid email address'),
            }
    )

    def clean_email(self):
        try:
            user = User.objects.get(email=self.cleaned_data['email'])
        except:
            raise forms.ValidationError(_("Sorry, but this email is not on our database."))

        self.user_cache = user
        return self.cleaned_data['email']


class SimpleEmailSubscribeForm(forms.Form):
    SIMPLE_SUBSCRIBE_CHOICES = (
        ('y',_('okay, let\'s try!')),
        ('n',_('no community email please, thanks'))
    )
    subscribe = forms.ChoiceField(widget=forms.widgets.RadioSelect(), \
                                error_messages={'required':_('please choose one of the options above')},
                                choices=SIMPLE_SUBSCRIBE_CHOICES)

    def save(self,user=None):
        EFF = EditUserEmailFeedsForm
        if self.cleaned_data['subscribe'] == 'y':
            email_settings_form = EFF()
            logging.debug('%s wants to subscribe' % user.username)
        else:
            email_settings_form = EFF(initial=EFF.NO_EMAIL_INITIAL)
        email_settings_form.save(user,save_unbound=True)

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
