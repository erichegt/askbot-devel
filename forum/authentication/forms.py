from forum.utils.forms import NextUrlField,  UserNameField,  UserEmailField
from forum.models import EmailFeedSetting, Question
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django import forms
from forum.forms import EditUserEmailFeedsForm
import logging

class SimpleRegistrationForm(forms.Form):
    next = NextUrlField()
    username = UserNameField()
    email = UserEmailField()


class SimpleEmailSubscribeForm(forms.Form):
    SIMPLE_SUBSCRIBE_CHOICES = (
        ('y',_('okay, let\'s try!')),
        ('n',_('no OSQA community email please, thanks'))
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
