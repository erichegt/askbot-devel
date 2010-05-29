from django.db import models
from base import MetaContent, UserContent
from base import render_post_text_and_get_newly_mentioned_users
from base import save_content
from forum import const
import datetime

class VoteManager(models.Manager):
    def get_up_vote_count_from_user(self, user):
        if user is not None:
            return self.filter(user=user, vote=1).count()
        else:
            return 0

    def get_down_vote_count_from_user(self, user):
        if user is not None:
            return self.filter(user=user, vote=-1).count()
        else:
            return 0

    def get_votes_count_today_from_user(self, user):
        if user is not None:
            today = datetime.date.today()
            return self.filter(user=user, voted_at__range=(today, today + datetime.timedelta(1))).count()
        else:
            return 0


class Vote(MetaContent, UserContent):
    VOTE_UP = +1
    VOTE_DOWN = -1
    VOTE_CHOICES = (
        (VOTE_UP,   u'Up'),
        (VOTE_DOWN, u'Down'),
    )

    vote           = models.SmallIntegerField(choices=VOTE_CHOICES)
    voted_at       = models.DateTimeField(default=datetime.datetime.now)

    objects = VoteManager()

    class Meta(MetaContent.Meta):
        unique_together = ('content_type', 'object_id', 'user')
        db_table = u'vote'

    def __unicode__(self):
        return '[%s] voted at %s: %s' %(self.user, self.voted_at, self.vote)

    def is_upvote(self):
        return self.vote == self.VOTE_UP

    def is_downvote(self):
        return self.vote == self.VOTE_DOWN

    def is_opposite(self, vote_type):
        assert(vote_type in (self.VOTE_UP, self.VOTE_DOWN))
        return self.vote != vote_type


class FlaggedItemManager(models.Manager):
    def get_flagged_items_count_today(self, user):
        if user is not None:
            today = datetime.date.today()
            return self.filter(user=user, flagged_at__range=(today, today + datetime.timedelta(1))).count()
        else:
            return 0

class FlaggedItem(MetaContent, UserContent):
    """A flag on a Question or Answer indicating offensive content."""
    flagged_at     = models.DateTimeField(default=datetime.datetime.now)

    objects = FlaggedItemManager()

    class Meta(MetaContent.Meta):
        unique_together = ('content_type', 'object_id', 'user')
        db_table = u'flagged_item'

    def __unicode__(self):
        return '[%s] flagged at %s' %(self.user, self.flagged_at)

class Comment(MetaContent, UserContent):
    comment = models.CharField(max_length = const.COMMENT_HARD_MAX_LENGTH)
    added_at = models.DateTimeField(default = datetime.datetime.now)
    html = models.CharField(max_length = const.COMMENT_HARD_MAX_LENGTH, default='')

    class Meta(MetaContent.Meta):
        ordering = ('-added_at',)
        db_table = u'comment'

    def get_origin_post(self):
        return self.content_object.get_origin_post()

    #todo: maybe remove this wnen post models are unified
    def get_text(self):
        return self.comment

    _render_text_and_get_newly_mentioned_users = \
        render_post_text_and_get_newly_mentioned_users

    _save = save_content

    def save(self,**kwargs):
        self._save(urlize_content = True)

    def get_updated_activity_type(self):
        if self.content_object.__class__.__name__ == 'Question':
            return const.TYPE_ACTIVITY_COMMENT_QUESTION
        elif self.content_object.__class__.__name__ == 'Answer':
            return const.TYPE_ACTIVITY_COMMENT_ANSWER

    def get_potentially_interested_users(self):
        users = set()
        users.update(
                    #get authors of parent object and all associated comments
                    self.content_object.get_author_list(
                            include_comments = True,
                        )
                )

        users -= set([self.user])#remove activity user
        return list(users)

    def delete(self, **kwargs):
        #todo: not very good import in models of other models
        #todo: potentially a circular import
        from forum.models.user import Activity
        Activity.objects.get_mentions(
                            mentioned_in = self
                        ).delete()
        super(Comment,self).delete(**kwargs)

    def get_absolute_url(self):
        origin_post = self.get_origin_post()
        return '%s#comment-%d' % (origin_post.get_absolute_url(), self.id)

    def get_latest_revision_number(self):
        return 1

    def __unicode__(self):
        return self.comment
