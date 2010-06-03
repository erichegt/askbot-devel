import datetime
import logging
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.sitemaps import ping_google
from django.db import models
from forum.models.meta import Comment, Vote, FlaggedItem

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

    html = models.TextField(null=True)#html rendition of the latest revision
    text = models.TextField(null=True)#denormalized copy of latest revision
    comments = generic.GenericRelation(Comment)
    votes = generic.GenericRelation(Vote)
    flagged_items = generic.GenericRelation(FlaggedItem)

    _use_markdown = True
    _urlize = False

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

    #todo: maybe remove this wnen post models are unified
    def get_text(self):
        return self.text

    def add_comment(self, comment=None, user=None, added_at=None):
        if added_at is None:
            added_at = datetime.datetime.now()
        if None in (comment ,user):
            raise Exception('arguments comment and user are required')

        #Comment = models.get_model('forum','Comment')#todo: forum hardcoded
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
        return self.revisions.all().order_by('-revised_at')[0]

    def get_latest_revision_number(self):
        return self.get_latest_revision().revision

    def get_last_author(self):
        return self.last_edited_by

    def get_time_of_last_edit(self):
        if self.last_edited_at:
            return self.last_edited_at
        else:
            return self.added_at

    def get_author_list(self, include_comments = False, recursive = False, exclude_list = None):
        authors = set()
        authors.update([r.author for r in self.revisions.all()])
        if include_comments:
            authors.update([c.user for c in self.comments.all()])
        if recursive:
            if hasattr(self, 'answers'):
                for a in self.answers.exclude(deleted = True):
                    authors.update(a.get_author_list( include_comments = include_comments ) )
        if exclude_list:
            authors -= set(exclude_list)
        return list(authors)

    def passes_tag_filter_for_user(self, user):
        tags = self.get_origin_post().tags.all()

        if self.tag_filter_setting == 'interesting':
            #at least some of the tags must be marked interesting
            return self.tag_selections.exists(tag__in = tags, reason = 'good')

        elif self.tag_filter_setting == 'ignored':
            #at least one tag must be ignored
            if self.tag_selections.exists(tag__in = tags, reason = 'bad'):
                return False
            else:
                return True

        else:
            raise ValueError(
                        'unexpected User.tag_filter_setting %s' \
                        % self.tag_filter_setting
                    )

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
