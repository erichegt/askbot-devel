from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.conf import settings as askbot_settings
from askbot.models import Tag
from askbot.models.group import get_groups
from askbot.forms import FormWithHideableFields, TagNamesField
from askbot.conf import settings as askbot_settings
from django import forms

DEFAULT_INNER_STYLE = ''

DEFAULT_OUTER_STYLE = ''

DEFAULT_QUESTION_STYLE = '''
@import url('http://fonts.googleapis.com/css?family=Yanone+Kaffeesatz:300,400,700');
body {
    overflow: hidden;
}

#container {
    width: 200px;
    height: 350px;
}
ul {
    list-style: none;
    padding: 5px;
    margin: 5px;
}
li {
    border-bottom: #CCC 1px solid;
    padding-bottom: 5px;
    padding-top: 5px;
}
li:last-child {
    border: none;
}
a {
    text-decoration: none;
    color: #464646;
    font-family: 'Yanone Kaffeesatz', sans-serif;
    font-size: 15px;
}
'''


class AskWidget(models.Model):
    '''stores widgets styles and options'''
    title = models.CharField(max_length=100)
    group = models.ForeignKey(Tag, null=True, blank=True,
                              related_name='groups')
    tag = models.ForeignKey(Tag, null=True, blank=True)

    include_text_field = models.BooleanField(default=False, blank=True)

    inner_style = models.TextField(default=DEFAULT_INNER_STYLE, blank=True)
    outer_style= models.TextField(default=DEFAULT_OUTER_STYLE, blank=True)

    class Meta:
        app_label = 'askbot'

    def __unicode__(self):
        return "Widget: %s" % self.title

SEARCH_ORDER_BY = (
                    ('-added_at', _('date descendant')),
                    ('added_at', _('date ascendant')),
                    ('-last_activity_at', _('activity descendant')),
                    ('last_activity_at', _('activity ascendant')),
                    ('-answer_count', _('answers descendant')),
                    ('answer_count', _('answers ascendant')),
                    ('-score', _('votes descendant')),
                    ('score', _('votes ascendant')),
                  )

class QuestionWidget(models.Model):
    title = models.CharField(max_length=100)
    question_number = models.PositiveIntegerField(default=7)
    tagnames = models.CharField(_('tags'), max_length=50)
    group = models.ForeignKey(Tag, null=True, blank=True)
    search_query = models.CharField(
        max_length=50, null=True, blank=True, default=''
    )
    order_by = models.CharField(max_length=18,
            choices=SEARCH_ORDER_BY, default='-added_at')
    style = models.TextField(_('css for the widget'),
            default=DEFAULT_QUESTION_STYLE, blank=True)

    class Meta:
        app_label = 'askbot'

#FORMS
class CreateAskWidgetForm(forms.ModelForm, FormWithHideableFields):
    inner_style = forms.CharField(
                        widget=forms.Textarea,
                        required=False,
                        initial=DEFAULT_INNER_STYLE
                    )
    outer_style = forms.CharField(
                        widget=forms.Textarea,
                        required=False,
                        initial=DEFAULT_OUTER_STYLE
                    )

    group = forms.ModelChoiceField(queryset=get_groups().exclude(name__startswith='_internal'),
            required=False)
    tag = forms.ModelChoiceField(queryset=Tag.objects.get_content_tags(),
            required=False)

    def __init__(self, *args, **kwargs):
        super(CreateAskWidgetForm, self).__init__(*args, **kwargs)
        if not askbot_settings.GROUPS_ENABLED:
            self.hide_field('group')

    class Meta:
        model = AskWidget

class CreateQuestionWidgetForm(forms.ModelForm, FormWithHideableFields):
    tagnames = TagNamesField()
    group = forms.ModelChoiceField(queryset=get_groups().exclude(name__startswith='_internal'),
            required=False)

    class Meta:
        model = QuestionWidget
