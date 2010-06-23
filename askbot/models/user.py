from hashlib import md5
import string
from random import Random
import datetime
import logging
from django.db import models
from django.db.backends.dummy.base import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot import const
from askbot.utils import functions

class ResponseAndMentionActivityManager(models.Manager):
    def get_query_set(self):
        response_types = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
        response_types += (const.TYPE_ACTIVITY_MENTION, )
        return super(
                    ResponseAndMentionActivityManager,
                    self
                ).get_query_set().filter(
                    activity_type__in = response_types
                )

class ActivityManager(models.Manager):
    def get_all_origin_posts(self):
        #todo: redo this with query sets
        origin_posts = set()
        for m in self.all():
            post = m.content_object
            if post and hasattr(post, 'get_origin_post'):
                origin_posts.add(post.get_origin_post())
            else:
                logging.debug(
                            'method get_origin_post() not implemented for %s' \
                            % unicode(post)
                        )
        return list(origin_posts)

    def create_new_mention(
                self,
                mentioned_by = None,
                mentioned_whom = None,
                mentioned_at = None,
                mentioned_in = None,
                reported = None
            ): 

        #todo: automate this using python inspect module
        kwargs = dict()

        kwargs['activity_type'] = const.TYPE_ACTIVITY_MENTION

        if mentioned_at:
            #todo: handle cases with rich lookups here like __lt
            kwargs['active_at'] = mentioned_at

        if mentioned_by:
            kwargs['user'] = mentioned_by

        if mentioned_in:
            if functions.is_iterable(mentioned_in):
                raise NotImplementedError('mentioned_in only works for single items')
            else:
                post_content_type = ContentType.objects.get_for_model(mentioned_in)
                kwargs['content_type'] = post_content_type
                kwargs['object_id'] = mentioned_in.id

        if reported == True:
            kwargs['is_auditted'] = True
        else:
            kwargs['is_auditted'] = False

        mention_activity = Activity(**kwargs)
        mention_activity.save()

        if mentioned_whom:
            if functions.is_iterable(mentioned_whom):
                raise NotImplementedError('cannot yet mention multiple people at once')
            else:
                mention_activity.receiving_users.add(mentioned_whom)

        return mention_activity

    def get_mentions(
                self, 
                mentioned_by = None,
                mentioned_whom = None,
                mentioned_at = None,
                mentioned_in = None,
                reported = None,
                mentioned_at__gt = None,
            ):
        """extract mention-type activity objects
        todo: implement better rich field lookups
        """

        kwargs = dict()

        kwargs['activity_type'] = const.TYPE_ACTIVITY_MENTION

        if mentioned_at:
            #todo: handle cases with rich lookups here like __lt
            kwargs['active_at'] = mentioned_at
        elif mentioned_at__gt:
            kwargs['active_at__gt'] = mentioned_at__gt

        if mentioned_by:
            kwargs['user'] = mentioned_by

        if mentioned_whom:
            if functions.is_iterable(mentioned_whom):
                kwargs['receiving_users__in'] = mentioned_whom
            else:
                kwargs['receiving_users__in'] = (mentioned_whom,)

        if mentioned_in:
            if functions.is_iterable(mentioned_in):
                it = iter(mentioned_in)
                raise NotImplementedError('mentioned_in only works for single items')
            else:
                post_content_type = ContentType.objects.get_for_model(mentioned_in)
                kwargs['content_type'] = post_content_type
                kwargs['object_id'] = mentioned_in.id

        if reported == True:
            kwargs['is_auditted'] = True
        else:
            kwargs['is_auditted'] = False

        return self.filter(**kwargs)


class Activity(models.Model):
    """
    We keep some history data for user activities
    """
    user = models.ForeignKey(User)
    receiving_users = models.ManyToManyField(User, related_name='received_activity')
    activity_type = models.SmallIntegerField(choices = const.TYPE_ACTIVITY)
    active_at = models.DateTimeField(default=datetime.datetime.now)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    is_auditted = models.BooleanField(default=False)

    objects = ActivityManager()
    responses_and_mentions = ResponseAndMentionActivityManager()

    def __unicode__(self):
        return u'[%s] was active at %s' % (self.user.username, self.active_at)

    class Meta:
        app_label = 'askbot'
        db_table = u'activity'

    def get_mentioned_user(self):
        assert(self.activity_type == const.TYPE_ACTIVITY_MENTION)
        user_qs = self.receiving_users.all()
        assert(len(user_qs) == 1)
        return user_qs[0]

    def get_absolute_url(self):
        return self.content_object.get_absolute_url()

class EmailFeedSetting(models.Model):
    DELTA_TABLE = {
        'i':datetime.timedelta(-1),#instant emails are processed separately
        'd':datetime.timedelta(1),
        'w':datetime.timedelta(7),
        'n':datetime.timedelta(-1),
    }
    FEED_TYPES = (
                    ('q_all',_('Entire askbot')),
                    ('q_ask',_('Questions that I asked')),
                    ('q_ans',_('Questions that I answered')),
                    ('q_sel',_('Individually selected questions')),
                    ('m_and_c',_('Mentions and comment responses')),
                    )
    UPDATE_FREQUENCY = (
                    ('i',_('Instantly')),
                    ('d',_('Daily')),
                    ('w',_('Weekly')),
                    ('n',_('No email')),
                   )


    subscriber = models.ForeignKey(User, related_name='notification_subscriptions')
    feed_type = models.CharField(max_length=16,choices=FEED_TYPES)
    frequency = models.CharField(
                                    max_length=8,
                                    choices=const.NOTIFICATION_DELIVERY_SCHEDULE_CHOICES,
                                    default='n',
                                )
    added_at = models.DateTimeField(auto_now_add=True)
    reported_at = models.DateTimeField(null=True)

    #functions for rich comparison
    #PRECEDENCE = ('i','d','w','n')#the greater ones are first
    #def __eq__(self, other):
    #    return self.id == other.id

#    def __eq__(self, other):
#        return self.id != other.id

#    def __gt__(self, other):
#        return PRECEDENCE.index(self.frequency) < PRECEDENCE.index(other.frequency) 

#    def __lt__(self, other):
#        return PRECEDENCE.index(self.frequency) > PRECEDENCE.index(other.frequency) 

#    def __gte__(self, other):
#        if self.__eq__(other):
#            return True
#        else:
#            return self.__gt__(other)

#    def __lte__(self, other):
#        if self.__eq__(other):
#            return True
#        else:
#            return self.__lt__(other)

    def save(self,*args,**kwargs):
        type = self.feed_type
        subscriber = self.subscriber
        similar = self.__class__.objects.filter(
                                            feed_type=type,
                                            subscriber=subscriber
                                        ).exclude(pk=self.id)
        if len(similar) > 0:
            raise IntegrityError('email feed setting already exists')
        super(EmailFeedSetting,self).save(*args,**kwargs)

    def get_previous_report_cutoff_time(self):
        now = datetime.datetime.now()
        return now - self.DELTA_TABLE[self.frequency]

    def should_send_now(self):
        now = datetime.datetime.now()
        cutoff_time = self.get_previous_report_cutoff_time()
        if self.reported_at == None or self.reported_at <= cutoff_time:
            return True
        else:
            return False

    def mark_reported_now(self):
        self.reported_at = datetime.datetime.now()
        self.save()

    class Meta:
        app_label = 'askbot'

#class AuthKeyUserAssociation(models.Model):
#    key = models.CharField(max_length=255,null=False,unique=True)
#    provider = models.CharField(max_length=64)#string 'yahoo', 'google', etc.
#    user = models.ForeignKey(User, related_name="auth_keys")
#    added_at = models.DateTimeField(default=datetime.datetime.now)
#
#    class Meta:
#        app_label = 'askbot'
