import random
import string

from django.db import models
from django.contrib.auth.models import User

from askbot.models.post import Post
from askbot.models.base import BaseQuerySetManager

class ReplyAddressManager(BaseQuerySetManager):
    
    def create_new(self, post, user):
        reply_address = ReplyAddress(post = post, user = user, allowed_from_email = user.email)
        while True:
            reply_address.address = ''.join(random.choice(string.letters +
                string.digits) for i in xrange(random.randint(12, 25)))
            if ReplyAddress.objects.filter(address = reply_address.address).count() == 0:
                break
        reply_address.save()
        return reply_address
			

class ReplyAddress(models.Model):
    address = models.CharField(max_length = 25, unique = True)
    post = models.ForeignKey(Post)
    user = models.ForeignKey(User)
    allowed_from_email = models.EmailField(max_length = 150)
    used_at = models.DateTimeField(null = True, default = None)

    objects = ReplyAddressManager()

    class Meta:
        app_label = 'askbot'
        db_table = 'askbot_replyaddress'