from base import *
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from hashlib import md5
import string
from random import Random

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

from forum.utils.time import one_day_from_now

class ValidationHashManager(models.Manager):
    def _generate_md5_hash(self, user, type, hash_data, seed):
        return md5("%s%s%s%s" % (seed, "".join(map(str, hash_data)), user.id, type)).hexdigest()

    def create_new(self, user, type, hash_data=[], expiration=None):
        seed = ''.join(Random().sample(string.letters+string.digits, 12))
        hash = self._generate_md5_hash(user, type, hash_data, seed)

        obj = ValidationHash(hash_code=hash, seed=seed, user=user, type=type)

        if expiration is not None:
            obj.expiration = expiration

        try:
            obj.save()
        except:
            return None
            
        return obj

    def validate(self, hash, user, type, hash_data=[]):
        try:
            obj = self.get(hash_code=hash)
        except:
            return False

        if obj.type != type:
            return False

        if obj.user != user:
            return False

        valid = (obj.hash_code == self._generate_md5_hash(obj.user, type, hash_data, obj.seed))

        if valid:
            if obj.expiration < datetime.datetime.now():
                obj.delete()
                return False
            else:
                obj.delete()
                return True

        return False

class ValidationHash(models.Model):
    #todo: was 256 chars - is that important?
    #on mysql 255 is max for unique=True
    hash_code = models.CharField(max_length=255,unique=True)
    seed = models.CharField(max_length=12)
    expiration = models.DateTimeField(default=one_day_from_now)
    type = models.CharField(max_length=12)
    user = models.ForeignKey(User)

    objects = ValidationHashManager()

    class Meta:
        unique_together = ('user', 'type')
        app_label = 'forum'

    def __str__(self):
        return self.hash_code

class AuthKeyUserAssociation(models.Model):
    key = models.CharField(max_length=255,null=False,unique=True)
    provider = models.CharField(max_length=64)#string 'yahoo', 'google', etc.
    user = models.ForeignKey(User, related_name="auth_keys")
    added_at = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label = 'forum'
