from utils.forms import NextUrlField, UserNameField, UserEmailField, SetPasswordForm
from django import forms
from django.forms import ValidationError
from models import User as MWUser
from models import TITLE_CHOICES
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.contrib.formtools.wizard import FormWizard
from forum.forms import EditUserEmailFeedsForm, SimpleEmailSubscribeForm
from django.forms import ValidationError
from recaptcha_django import ReCaptchaField
from utils.forms import StrippedNonEmptyCharField
from forum.templatetags import extra_tags as forum_extra_tags

#make better translations in your language django.po
EMAIL_FEED_CHOICES = (
    ('y',_('okay, let\'s try!')),
    ('n',_('no OSQA community email please, thanks'))
)

wiki_account_taken_msg = _('Wiki site already has this account, if it is yours perhaps you can '
                            'just try to log in with it?<br/>'
                            'Otherwise, please pick another login name.')

class RegisterForm(SetPasswordForm, SimpleEmailSubscribeForm):
    login_name = UserNameField(label=_('Login name'), \
                            db_model=MWUser, \
                            db_field='user_name', \
                            error_messages={ \
                                'required':_('Please enter login name above, it is required for the Wiki site'), \
                                'taken': mark_safe(wiki_account_taken_msg) \
                                }
                            )
    next = NextUrlField() 
    email = UserEmailField()
    screen_name = UserNameField(label=mark_safe(_('Please type your nickname below')), \
                                skip_clean=True, \
                                required=False)
    first_name = StrippedNonEmptyCharField(max_length=255,label=mark_safe(_('First name')),
                                    error_messages={'required':_('First name is required')}
                                  )
    last_name = StrippedNonEmptyCharField(max_length=255,label=_('Last name'),
                                    error_messages={'required':_('Last name is required')}
                                 )
    #cannot be just "title" because there would be a conflict with "title" field used for MW!!!
    user_title = forms.ChoiceField(choices=TITLE_CHOICES, label=_('Title (optional)'))
    use_separate_screen_name = forms.BooleanField(
                                    label=mark_safe(_('I prefer (or have to) to use a separate forum screen name')),
                                    required=False,
                                 )
    #subscribe = forms.ChoiceField(widget=forms.widgets.RadioSelect, \
    #                            error_messages={'required':_('please choose one of the options above')},
    #                            choices= EMAIL_FEED_CHOICES)
    recaptcha = ReCaptchaField()

    class Media:
        css={'all':(forum_extra_tags.href('/content/style/mediawiki-login.css'),),}
        js=(forum_extra_tags.href('/content/js/mediawiki-login.js'),)

    def add_screen_name_error(self, err):
        if 'screen_name' in self.cleaned_data:
            del self.cleaned_data['screen_name']
        error_list = self._errors.get('screen_name',forms.util.ErrorList([]))
        if isinstance(err, forms.util.ErrorList):
            error_list.extend(err)
        else:
            error_list.append(err)
        self._errors['screen_name'] = error_list

    def clean(self):
        #this method cleans screen_name and use_separate_screen_name
        screen_name = self.cleaned_data.get('screen_name', '')
            
        if 'use_separate_screen_name' in self.cleaned_data \
            and self.cleaned_data['use_separate_screen_name']: 
            if screen_name == '':
                msg = _('please enter an alternative screen name or uncheck the box above')
                self.add_screen_name_error(msg)
            else:
                try:
                    screen_name = self.fields['screen_name'].clean(screen_name)
                    self.final_clean_screen_name(screen_name)
                except ValidationError, e:
                    self.add_screen_name_error(e)
        else:
            if screen_name != '':
                self.add_screen_name_error(_('sorry, to use alternative screen name, please confirm it by checking the box above'))
            else:
                #build screen name from first and last names
                first = self.cleaned_data.get('first_name',None)
                last = self.cleaned_data.get('last_name',None)
                if first and last:
                    screen_name = u'%s %s' % (first,last)
                    self.final_clean_screen_name(screen_name)
        return self.cleaned_data

    def final_clean_screen_name(self,name):
        try:
            u = User.objects.get(username=name)
            msg = _('Screen name <strong>%(real_name)s</strong> is somehow already taken on the forum.<br/>'
                    'Unfortunately you will have to pick a separate screen name, but of course '
                    'there is no need to change the first name and last name entries.<br/>'
                    'Please send us your feedback if you feel there might be a mistake. '
                    'Sorry for the inconvenience.')\
                    % {'real_name':name}
            self.add_screen_name_error(mark_safe(msg))
        except:
            self.cleaned_data['screen_name'] = name 

    #overridden validation for UserNameField
    def clean_login_name(self):
        try:
            MWUser.objects.get(user_name=self.cleaned_data['login_name'])
            del self.cleaned_data['login_name']
            raise ValidationError(_('sorry this login name is already taken, please try another'))
        except:
            return self.cleaned_data['login_name']

class RegisterFormWizard(FormWizard):
    def done(self, request, form_list):
        data = form_list[0].cleaned_data
        login_name = data['login_name']
        password = data['password']
        first_name = data['first_name']
        last_name = data['last_name']
        screen_name = data['screen_name']
        email = data['email']
        subscribe = data['subscribe']
        next = data['next']

        #register mediawiki user
        mwu = MWUser(
                       user_name=login_name,
                       user_password=password,
                       user_first_name = first_name,
                       user_last_name = last_name,
                       user_email = email
                    )
        mwu.save()

        #register local user
        User.objects.create_user(screen_name, email, password)
        u = authenticate(username=screen_name, password=password)
        u.mediawiki_user = mwu
        u.save()

        #save email feed settings
        EFF = EditUserEmailFeedsForm
        if subscribe == 'y':
            email_settings_form = EFF()
        else:
            email_settings_form = EFF(initial=EFF.NO_EMAIL_INITIAL)
        email_settings_form.save(u)

        #create welcome message
        u.message_set.create(message=_('Welcome to Q&A forum!'))
        return HttpResponseRedirect(next)

    def get_template(self, step):
        if step == 0:
            return 'mediawiki/mediawiki_signup.html'
        elif step == 1:
            return 'notarobot.html'
