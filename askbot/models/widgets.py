from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.conf import settings as askbot_settings
from askbot.models import Tag
from askbot.models.tag import get_groups
from django import forms

DEFAULT_INNER_STYLE = ''

DEFAULT_OUTER_STYLE = ''

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

class CreateAskWidgetForm(forms.ModelForm):
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

    class Meta:
        model = AskWidget
