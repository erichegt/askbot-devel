import datetime
import hashlib
from urllib import quote_plus, urlencode
from django.db import models
from django.utils.http import urlquote  as django_urlquote
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _
from django.contrib.sitemaps import ping_google
import django.dispatch
from django.conf import settings
from forum.utils import markup
from django.utils import html
import logging

#todo: following methods belong to a future common post class
def render_post_text_and_get_newly_mentioned_users(post, 
                                        urlize_content = False):

    text = post.get_text()

    if urlize_content:
        text = html.urlize(text)

    if '@' not in text:
        return list()

    from forum.models.user import Activity

    mentioned_by = post.get_last_author()

    op = post.get_origin_post()
    anticipated_authors = op.get_author_list( include_comments = True, recursive = True )

    extra_name_seeds = markup.extract_mentioned_name_seeds(text)
    extra_authors = set()
    for name_seed in extra_name_seeds:
        extra_authors.update(User.objects.filter(username__startswith = name_seed))

    #it is important to preserve order here so that authors of post get mentioned first
    anticipated_authors += list(extra_authors)

    mentioned_authors, post.html = markup.mentionize_text(text, anticipated_authors)

    #maybe delete some previous mentions
    if self.id != None:
        #only look for previous mentions if post was already saved before
        prev_mention_qs = Activity.objects.get_mentions(
                                    mentioned_in = post
                                )
        new_set = set(mentioned_authors)
        for mention in prev_mention_qs:
            delta_set = set(mention.receiving_users.all()) - new_set
            if not delta_set:
                mention.delete()
                new_set -= delta_set

        mentioned_authors = list(new_set)

    return mentioned_authors

def save_content(self, urlize_content = False, **kwargs):
    """generic save method to use with posts
    """

    new_mentions = self._render_text_and_get_newly_mentioned_users( 
                                                            urlize_content
                                                        )

    from forum.models.user import Activity

    #this save must precede saving the mention activity
    super(self.__class__, self).save(**kwargs)

    post_author = self.get_last_author()

    for u in new_mentions:
        Activity.objects.create_new_mention(
                                mentioned_whom = u,
                                mentioned_in = self,
                                mentioned_by = post_author
                            )


    #todo: this is handled in signal because models for posts
    #are too spread out
    from forum.models import signals
    signals.post_updated.send(
                    post = self, 
                    newly_mentioned_users = new_mentions, 
                    sender = self.__class__
                )

    try:
        ping_google()
    except Exception:
        logging.debug('problem pinging google did you register you sitemap with google?')

class UserContent(models.Model):
    user = models.ForeignKey(User, related_name='%(class)ss')

    class Meta:
        abstract = True
        app_label = 'forum'

    def get_last_author(self):
        return self.user

class MetaContent(models.Model):
    """
        Base class for Vote, Comment and FlaggedItem
    """
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'forum'

class DeletableContent(models.Model):
    deleted     = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    deleted_by  = models.ForeignKey(User, null=True, blank=True, related_name='deleted_%(class)ss')

    class Meta:
        abstract = True
        app_label = 'forum'


class ContentRevision(models.Model):
    """
        Base class for QuestionRevision and AnswerRevision
    """
    revision   = models.PositiveIntegerField()
    author     = models.ForeignKey(User, related_name='%(class)ss')
    revised_at = models.DateTimeField()
    summary    = models.CharField(max_length=300, blank=True)
    text       = models.TextField()

    class Meta:
        abstract = True
        app_label = 'forum'


class AnonymousContent(models.Model):
    """
        Base class for AnonymousQuestion and AnonymousAnswer
    """
    session_key = models.CharField(max_length=40)  #session id for anonymous questions
    wiki = models.BooleanField(default=False)
    added_at = models.DateTimeField(default=datetime.datetime.now)
    ip_addr = models.IPAddressField(max_length=21) #allow high port numbers
    author = models.ForeignKey(User,null=True)
    text = models.TextField()
    summary = models.CharField(max_length=180)

    class Meta:
        abstract = True
        app_label = 'forum'
