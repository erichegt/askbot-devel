from base import *

from django.utils.translation import ugettext as _

class Activity(models.Model):
    """
    We keep some history data for user activities
    """
    user = models.ForeignKey(User)
    activity_type = models.SmallIntegerField(choices=TYPE_ACTIVITY)
    active_at = models.DateTimeField(default=datetime.datetime.now)
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    is_auditted    = models.BooleanField(default=False)

    def __unicode__(self):
        return u'[%s] was active at %s' % (self.user.username, self.active_at)

    class Meta:
        app_label = 'forum'
        db_table = u'activity'

class EmailFeedSetting(models.Model):
    DELTA_TABLE = {
        'w':datetime.timedelta(7),
        'd':datetime.timedelta(1),
        'n':datetime.timedelta(-1),
    }
    FEED_TYPES = (
                    ('q_all',_('Entire forum')),
                    ('q_ask',_('Questions that I asked')),
                    ('q_ans',_('Questions that I answered')),
                    ('q_sel',_('Individually selected questions')),
                    )
    UPDATE_FREQUENCY = (
                    ('w',_('Weekly')),
                    ('d',_('Daily')),
                    ('n',_('No email')),
                   )
    subscriber = models.ForeignKey(User)
    feed_type = models.CharField(max_length=16,choices=FEED_TYPES)
    frequency = models.CharField(max_length=8,choices=UPDATE_FREQUENCY,default='n')
    added_at = models.DateTimeField(auto_now_add=True)
    reported_at = models.DateTimeField(null=True)

    def save(self,*args,**kwargs):
        type = self.feed_type
        subscriber = self.subscriber
        similar = self.__class__.objects.filter(feed_type=type,subscriber=subscriber).exclude(pk=self.id)
        if len(similar) > 0:
            raise IntegrityError('email feed setting already exists')
        super(EmailFeedSetting,self).save(*args,**kwargs)

    class Meta:
        app_label = 'forum'

class AnonymousEmail(models.Model):
    #validation key, if used
    key = models.CharField(max_length=32)
    email = models.EmailField(null=False,unique=True)
    isvalid = models.BooleanField(default=False)

    class Meta:
        app_label = 'forum'


class AuthKeyUserAssociation(models.Model):
    key = models.CharField(max_length=256,null=False,unique=True)
    provider = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    added_at = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label = 'forum'
        
    