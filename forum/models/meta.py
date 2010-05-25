from base import *
from forum import const
from django.utils.html import urlize
from forum.models import signals

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

    def save(self,**kwargs):
        print 'before first save'
        super(Comment,self).save(**kwargs)
        print 'after first save'
        from forum.models.utils import mentionize
        self.html = mentionize(urlize(self.comment, nofollow=True), context_object = self)
        print 'mentionized'
        #todo - try post_save to install mentions
        super(Comment,self).save(**kwargs)#have to save twice!!, b/c need id for generic relation

        signals.comment_post_save.send(instance = self, sender = Comment)

        try:
            ping_google()
        except Exception:
            logging.debug('problem pinging google did you register you sitemap with google?')

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

    get_newly_mentioned_users = get_newly_mentioned_users_in_post

    def __unicode__(self):
        return self.comment
