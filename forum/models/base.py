import datetime
import hashlib
from urllib import quote_plus, urlencode
from django.db import models, IntegrityError, connection, transaction
from django.utils.http import urlquote  as django_urlquote
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.db.models.signals import post_delete, post_save, pre_save
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.contrib.sitemaps import ping_google
import django.dispatch
from django.conf import settings
import logging

#todo: sphinx search import used to be here

from forum.const import *

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


from meta import Comment, Vote, FlaggedItem

class Content(models.Model):
    """
        Base class for Question and Answer
    """
    author = models.ForeignKey(User, related_name='%(class)ss')
    added_at = models.DateTimeField(default=datetime.datetime.now)

    wiki = models.BooleanField(default=False)
    wikified_at = models.DateTimeField(null=True, blank=True)

    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, related_name='locked_%(class)ss')
    locked_at = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(default=0)
    vote_up_count = models.IntegerField(default=0)
    vote_down_count = models.IntegerField(default=0)

    comment_count = models.PositiveIntegerField(default=0)
    offensive_flag_count = models.SmallIntegerField(default=0)

    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(User, null=True, blank=True, related_name='last_edited_%(class)ss')

    html = models.TextField(null=True)
    text = models.TextField(null=True) #denormalized copy of latest revision
    comments = generic.GenericRelation(Comment)
    votes = generic.GenericRelation(Vote)
    flagged_items = generic.GenericRelation(FlaggedItem)

    class Meta:
        abstract = True
        app_label = 'forum'

    def save(self,**kwargs):
        super(Content,self).save(**kwargs)
        try:
            ping_google()
        except Exception:
            logging.debug('problem pinging google did you register you sitemap with google?')

    def get_comments(self):
        comments = self.comments.all().order_by('id')
        return comments

    def add_comment(self, comment=None, user=None, added_at=None):
        if added_at is None:
            added_at = datetime.datetime.now()
        if None in (comment ,user):
            raise Exception('arguments comment and user are required')

        Comment = models.get_model('forum','Comment')#todo: forum hardcoded
        comment = Comment(
                            content_object=self, 
                            comment=comment, 
                            user=user, 
                            added_at=added_at
                        )
        comment.save()
        self.comment_count = self.comment_count + 1
        self.save()

    def get_latest_revision(self):
        return self.revisions.all()[0]

    def get_last_author(self):
        return self.last_edited_by

    def get_author_list(self, include_comments = False, recursive = False, exclude_list = None):
        authors = set()
        authors.update([r.author for r in self.revisions.all()])
        if include_comments:
            authors.update([c.user for c in self.comments.all()])
        if recursive:
            if hasattr(self, 'answers'):
                for a in self.answers.all():
                    authors.update(a.get_author_list( include_comments = include_comments ) )
        if exclude_list:
            authors -= set(exclude_list)
        return list(authors)

    def post_get_last_update_info(self):#todo: rename this subroutine
            when = self.added_at
            who = self.author
            if self.last_edited_at and self.last_edited_at > when:
                when = self.last_edited_at
                who = self.last_edited_by
            comments = self.comments.all()
            if len(comments) > 0:
                for c in comments:
                    if c.added_at > when:
                        when = c.added_at
                        who = c.user
            return when, who
