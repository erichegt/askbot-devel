import re
from django import forms
from askbot import models
from askbot import const
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from askbot.utils.forms import NextUrlField, UserNameField
from askbot.deps.recaptcha_django import ReCaptchaField
from askbot.conf import settings as askbot_settings
import logging


class TitleField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(TitleField, self).__init__(*args, **kwargs)
        self.required = True
        self.widget = forms.TextInput(
                                attrs={'size' : 70, 'autocomplete' : 'off'}
                            )
        self.max_length = 255
        self.label  = _('title')
        self.help_text = _('please enter a descriptive title for your question')
        self.initial = ''

    def clean(self, value):
        if len(value) < 10:
            raise forms.ValidationError(_('title must be > 10 characters'))

        return value

class EditorField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(EditorField, self).__init__(*args, **kwargs)
        self.required = True
        self.widget = forms.Textarea(attrs={'id':'editor'})
        self.label  = _('content')
        self.help_text = u''
        self.initial = ''

    def clean(self, value):
        if len(value) < 10:
            raise forms.ValidationError(_('question content must be > 10 characters'))
        return value

class TagNamesField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(TagNamesField, self).__init__(*args, **kwargs)
        self.required = True
        self.widget = forms.TextInput(attrs={'size' : 50, 'autocomplete' : 'off'})
        self.max_length = 255
        self.label  = _('tags')
        #self.help_text = _('please use space to separate tags (this enables autocomplete feature)')
        self.help_text = _('Tags are short keywords, with no spaces within. Up to five tags can be used.')
        self.initial = ''

    def clean(self, value):
        value = super(TagNamesField, self).clean(value)
        data = value.strip()
        if len(data) < 1:
            raise forms.ValidationError(_('tags are required'))

        split_re = re.compile(const.TAG_SPLIT_REGEX)
        tag_strings = split_re.split(data)
        out_tag_list = []
        tag_count = len(tag_strings)
        if tag_count > askbot_settings.MAX_TAGS_PER_POST:
            max_tags = askbot_settings.MAX_TAGS_PER_POST
            msg = ungettext(
                        'please use %(tag_count)d tag or less',
                        'please use %(tag_count)d tags or less',
                        tag_count) % {'tag_count':max_tags}
            raise forms.ValidationError(msg)
        for tag in tag_strings:
            tag_length = len(tag)
            if tag_length > askbot_settings.MAX_TAG_LENGTH:
                #singular form is odd in english, but required for pluralization
                #in other languages
                msg = ungettext('each tag must be shorter than %(max_chars)d character',#odd but added for completeness
                                'each tag must be shorter than %(max_chars)d characters',
                                tag_length) % {'max_chars':tag_length}
                raise forms.ValidationError(msg)

            #todo - this needs to come from settings
            tagname_re = re.compile(const.TAG_REGEX, re.UNICODE)
            if not tagname_re.search(tag):
                raise forms.ValidationError(_('use-these-chars-in-tags'))
            #only keep unique tags
            if tag not in out_tag_list:
                out_tag_list.append(tag)
        return u' '.join(out_tag_list)

class WikiField(forms.BooleanField):
    def __init__(self, *args, **kwargs):
        super(WikiField, self).__init__(*args, **kwargs)
        self.required = False
        self.label  = _('community wiki')
        self.help_text = _('if you choose community wiki option, the question and answer do not generate points and name of author will not be shown')
    def clean(self, value):
        return value and askbot_settings.WIKI_ON

class EmailNotifyField(forms.BooleanField):
    def __init__(self, *args, **kwargs):
        super(EmailNotifyField, self).__init__(*args, **kwargs)
        self.required = False
        self.widget.attrs['class'] = 'nomargin'

class SummaryField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(SummaryField, self).__init__(*args, **kwargs)
        self.required = False
        self.widget = forms.TextInput(attrs={'size' : 50, 'autocomplete' : 'off'})
        self.max_length = 300
        self.label  = _('update summary:')
        self.help_text = _('enter a brief summary of your revision (e.g. fixed spelling, grammar, improved style, this field is optional)')

class ModerateUserForm(forms.ModelForm):
    is_approved = forms.BooleanField(label=_("Automatically accept user's contributions for the email updates"),
                                     required=False)

    def clean_is_approved(self):
        if 'is_approved' not in self.cleaned_data:
            self.cleaned_data['is_approved'] = False
        return self.cleaned_data['is_approved']

    class Meta:
        model = User
        fields = ('is_approved',)

class AdvancedSearchForm(forms.Form):
    #nothing must be required in this form
    #it is used by the main questions view
    scope = forms.ChoiceField(choices=const.POST_SCOPE_LIST, required=False)
    sort = forms.ChoiceField(choices=const.POST_SORT_METHODS, required=False)
    query = forms.CharField(max_length=256, required=False)
    reset_tags = forms.BooleanField(required=False)
    reset_author = forms.BooleanField(required=False)
    reset_query = forms.BooleanField(required=False)
    start_over = forms.BooleanField(required=False)
    tags = forms.CharField(max_length=256, required=False)
    author = forms.IntegerField(required=False)
    page_size = forms.ChoiceField(choices=const.PAGE_SIZE_CHOICES, required=False)
    page = forms.IntegerField(required=False)

    def clean_tags(self):
        if 'tags' in self.cleaned_data:
            tags_input = self.cleaned_data['tags'].strip()
            split_re = re.compile(const.TAG_SPLIT_REGEX)
            tag_strings = split_re.split(tags_input)
            tagname_re = re.compile(const.TAG_REGEX, re.UNICODE)
            out = set()
            for s in tag_strings:
                if tagname_re.search(s):
                    out.add(s)
            if len(out) > 0:
                self.cleaned_data['tags'] = out
            else:
                self.cleaned_data['tags'] = None
            return self.cleaned_data['tags']

    def clean_query(self):
        if 'query' in self.cleaned_data:
            q = self.cleaned_data['query'].strip()
            if q == '':
                q = None
            self.cleaned_data['query'] = q
            return self.cleaned_data['query']

    def clean_page_size(self):
        if 'page_size' in self.cleaned_data:
            if self.cleaned_data['page_size'] == '':
                self.cleaned_data['page_size'] = None
            else:
                page_size = self.cleaned_data['page_size']
                #by this time it is guaranteed to be castable as int
                self.cleaned_data['page_size'] = int(page_size)
            return self.cleaned_data['page_size']

    def clean(self):
        #todo rewrite
        if self.cleaned_data['scope'] == '':
            del self.cleaned_data['scope']
        if self.cleaned_data['tags'] is None:
            del self.cleaned_data['tags']
        if self.cleaned_data['sort'] == '':
            del self.cleaned_data['sort']
        if self.cleaned_data['query'] == None:
            del self.cleaned_data['query']
        if self.cleaned_data['reset_tags'] == False:
            del self.cleaned_data['reset_tags']
        if self.cleaned_data['reset_author'] == False:
            del self.cleaned_data['reset_author']
        if self.cleaned_data['reset_query'] == False:
            del self.cleaned_data['reset_query']
        if self.cleaned_data['start_over'] == False:
            del self.cleaned_data['start_over']
        if self.cleaned_data['author'] is None:
            del self.cleaned_data['author']
        if self.cleaned_data['page'] is None:
            del self.cleaned_data['page']
        if self.cleaned_data['page_size'] is None:
            del self.cleaned_data['page_size']
        return self.cleaned_data

class NotARobotForm(forms.Form):
    recaptcha = ReCaptchaField()

class FeedbackForm(forms.Form):
    name = forms.CharField(label=_('Your name:'), required=False)
    email = forms.EmailField(label=_('Email (not shared with anyone):'), required=False)
    message = forms.CharField(label=_('Your message:'), max_length=800,widget=forms.Textarea(attrs={'cols':60}))
    next = NextUrlField()

class AskForm(forms.Form):
    title  = TitleField()
    text   = EditorField()
    tags   = TagNamesField()
    wiki = WikiField()

    openid = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 40, 'class':'openid-input'}))
    user   = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    email  = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))

class AnswerForm(forms.Form):
    text   = EditorField()
    wiki   = WikiField()
    openid = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 40, 'class':'openid-input'}))
    user   = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    email  = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    email_notify = EmailNotifyField()
    def __init__(self, question, user, *args, **kwargs):
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.fields['email_notify'].widget.attrs['id'] = 'question-subscribe-updates'
        if question.wiki and askbot_settings.WIKI_ON:
            self.fields['wiki'].initial = True
        if user.is_authenticated():
            if user in question.followed_by.all():
                self.fields['email_notify'].initial = True
                return
        self.fields['email_notify'].initial = False


class CloseForm(forms.Form):
    reason = forms.ChoiceField(choices=const.CLOSE_REASONS)

class RetagQuestionForm(forms.Form):
    tags   = TagNamesField()
    # initialize the default values
    def __init__(self, question, *args, **kwargs):
        super(RetagQuestionForm, self).__init__(*args, **kwargs)
        self.fields['tags'].initial = question.tagnames

class RevisionForm(forms.Form):
    """
    Lists revisions of a Question or Answer
    """
    revision = forms.ChoiceField(widget=forms.Select(attrs={'style' : 'width:520px'}))

    def __init__(self, post, latest_revision, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)
        revisions = post.revisions.all().values_list(
            'revision', 'author__username', 'revised_at', 'summary')
        date_format = '%c'
        self.fields['revision'].choices = [
            (r[0], u'%s - %s (%s) %s' % (r[0], r[1], r[2].strftime(date_format), r[3]))
            for r in revisions]
        self.fields['revision'].initial = latest_revision.revision

class EditQuestionForm(forms.Form):
    title  = TitleField()
    text   = EditorField()
    tags   = TagNamesField()
    summary = SummaryField()

    #todo: this is odd that this form takes question as an argument
    def __init__(self, question, revision, *args, **kwargs):
        super(EditQuestionForm, self).__init__(*args, **kwargs)
        self.fields['title'].initial = revision.title
        self.fields['text'].initial = revision.text
        self.fields['tags'].initial = revision.tagnames
        # Once wiki mode is enabled, it can't be disabled
        if not question.wiki:
            self.fields['wiki'] = WikiField()

class EditAnswerForm(forms.Form):
    text = EditorField()
    summary = SummaryField()

    def __init__(self, answer, revision, *args, **kwargs):
        super(EditAnswerForm, self).__init__(*args, **kwargs)
        self.fields['text'].initial = revision.text

class EditUserForm(forms.Form):
    email = forms.EmailField(label=u'Email', help_text=_('this email does not have to be linked to gravatar'), required=True, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    if askbot_settings.EDITABLE_SCREEN_NAME:
        username = UserNameField(label=_('Screen name'))
    realname = forms.CharField(label=_('Real name'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    website = forms.URLField(label=_('Website'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    city = forms.CharField(label=_('Location'), required=False, max_length=255, widget=forms.TextInput(attrs={'size' : 35}))
    birthday = forms.DateField(label=_('Date of birth'), help_text=_('will not be shown, used to calculate age, format: YYYY-MM-DD'), required=False, widget=forms.TextInput(attrs={'size' : 35}))
    about = forms.CharField(label=_('Profile'), required=False, widget=forms.Textarea(attrs={'cols' : 60}))

    def __init__(self, user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        logging.debug('initializing the form')
        if askbot_settings.EDITABLE_SCREEN_NAME:
            self.fields['username'].initial = user.username
            self.fields['username'].user_instance = user
        self.fields['email'].initial = user.email
        self.fields['realname'].initial = user.real_name
        self.fields['website'].initial = user.website
        self.fields['city'].initial = user.location

        if user.date_of_birth is not None:
            self.fields['birthday'].initial = user.date_of_birth
        else:
            self.fields['birthday'].initial = '1990-01-01'
        self.fields['about'].initial = user.about
        self.user = user

    def clean_email(self):
        """For security reason one unique email in database"""
        if self.user.email != self.cleaned_data['email']:
            #todo dry it, there is a similar thing in openidauth
            if askbot_settings.EMAIL_UNIQUE == True:
                if 'email' in self.cleaned_data:
                    try:
                        User.objects.get(email = self.cleaned_data['email'])
                    except User.DoesNotExist:
                        return self.cleaned_data['email']
                    except User.MultipleObjectsReturned:
                        raise forms.ValidationError(_('this email has already been registered, please use another one'))
                    raise forms.ValidationError(_('this email has already been registered, please use another one'))
        return self.cleaned_data['email']

class TagFilterSelectionForm(forms.ModelForm):
    tag_filter_setting = forms.ChoiceField(choices=const.TAG_EMAIL_FILTER_CHOICES,
                                            initial='ignored',
                                            label=_('Choose email tag filter'),
                                            widget=forms.RadioSelect)
    class Meta:
        model = User
        fields = ('tag_filter_setting',)

    def save(self):
        before = self.instance.tag_filter_setting
        super(TagFilterSelectionForm, self).save()
        after = self.instance.tag_filter_setting #User.objects.get(pk=self.instance.id).tag_filter_setting
        if before != after:
            return True
        return False
        

class EmailFeedSettingField(forms.ChoiceField):
    def __init__(self, *arg, **kwarg):
        kwarg['choices'] = const.NOTIFICATION_DELIVERY_SCHEDULE_CHOICES
        kwarg['initial'] = askbot_settings.DEFAULT_NOTIFICATION_DELIVERY_SCHEDULE
        kwarg['widget'] = forms.RadioSelect
        super(EmailFeedSettingField, self).__init__(*arg, **kwarg)

class EditUserEmailFeedsForm(forms.Form):
    FORM_TO_MODEL_MAP = {
                    'all_questions':'q_all',
                    'asked_by_me':'q_ask',
                    'answered_by_me':'q_ans',
                    'individually_selected':'q_sel',
                    'mentions_and_comments':'m_and_c',
                }
    NO_EMAIL_INITIAL = {
                    'all_questions':'n',
                    'asked_by_me':'n',
                    'answered_by_me':'n',
                    'individually_selected':'n',
                    'mentions_and_comments':'n',
                }

    asked_by_me = EmailFeedSettingField(
                            label=_('Asked by me')
                        )
    answered_by_me = EmailFeedSettingField(
                            label=_('Answered by me')
                        )
    individually_selected = EmailFeedSettingField(
                            label=_('Individually selected')
                        )
    all_questions = EmailFeedSettingField(
                            label=_('Entire forum (tag filtered)'),
                        )

    mentions_and_comments = EmailFeedSettingField(
                            label=_('Comments and posts mentioning me'),
                        )

    def set_initial_values(self, user=None):
        KEY_MAP = dict([(v, k) for k, v in self.FORM_TO_MODEL_MAP.iteritems()])
        if user != None:
            settings = models.EmailFeedSetting.objects.filter(subscriber=user)
            initial_values = {}
            for setting in settings:
                feed_type = setting.feed_type
                form_field = KEY_MAP[feed_type]
                frequency = setting.frequency
                initial_values[form_field] = frequency
            self.initial = initial_values
        return self

    def reset(self):
        if self.is_bound:
            self.cleaned_data['all_questions'] = 'n'
            self.cleaned_data['asked_by_me'] = 'n'
            self.cleaned_data['answered_by_me'] = 'n'
            self.cleaned_data['individually_selected'] = 'n'
            self.cleaned_data['mentions_and_comments'] = 'n'
        self.initial = self.NO_EMAIL_INITIAL
        return self

    def save(self,user,save_unbound=False):
        """
            with save_unbound==True will bypass form validation and save initial values
        """
        changed = False
        for form_field, feed_type in self.FORM_TO_MODEL_MAP.items():
            s, created = models.EmailFeedSetting.objects.get_or_create(
                                                    subscriber=user,
                                                    feed_type=feed_type
                                                )
            if save_unbound:
                #just save initial values instead
                if form_field in self.initial:
                    new_value = self.initial[form_field]
                else:
                    new_value = self.fields[form_field].initial
            else:
                new_value = self.cleaned_data[form_field]
            if s.frequency != new_value:
                s.frequency = new_value
                s.save()
                changed = True
            else:
                if created:
                    s.save()
            if form_field == 'individually_selected':
                feed_type = ContentType.objects.get_for_model(models.Question)
                user.followed_questions.clear()
        return changed

class SimpleEmailSubscribeForm(forms.Form):
    SIMPLE_SUBSCRIBE_CHOICES = (
        ('y',_('okay, let\'s try!')),
        ('n',_('no community email please, thanks'))
    )
    subscribe = forms.ChoiceField(
            widget=forms.widgets.RadioSelect, 
            error_messages={'required':_('please choose one of the options above')},
            choices=SIMPLE_SUBSCRIBE_CHOICES
        )

    def save(self, user=None):
        EFF = EditUserEmailFeedsForm
        if self.cleaned_data['subscribe'] == 'y':
            email_settings_form = EFF()
            logging.debug('%s wants to subscribe' % user.username)
        else:
            email_settings_form = EFF(initial=EFF.NO_EMAIL_INITIAL)
        email_settings_form.save(user, save_unbound=True)
