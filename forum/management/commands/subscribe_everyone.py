from django.core.management.base import NoArgsCommand
from django.db import connection
from django.db.models import Q, F
from forum.models import *
from django.core.mail import EmailMessage
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
import datetime
from django.conf import settings

class Command(NoArgsCommand):
    def handle_noargs(self,**options):
        try:
            try:
                self.subscribe_everyone()
            except Exception, e:
                print e
        finally:
            connection.close()

    def subscribe_everyone(self):

        feed_type_info = EmailFeedSetting.FEED_TYPES
        for user in User.objects.all():
            for feed_type in feed_type_info:
                try:
                    feed_setting = EmailFeedSetting.objects.get(subscriber=user,feed_type = feed_type[0])
                except EmailFeedSetting.DoesNotExist:
                    feed_setting = EmailFeedSetting(subscriber=user,feed_type=feed_type[0])
                feed_setting.frequency = 'w'
                feed_setting.reported_at = None
                feed_setting.save()
