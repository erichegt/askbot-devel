from datetime import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User
from askbot.models.post import Post
from askbot.models.base import BaseQuerySetManager
from askbot.utils.file_utils import store_file
from askbot.conf import settings as askbot_settings

class ReplyAddressManager(BaseQuerySetManager):

    def get_unused(self, address, allowed_from_email):
        return self.get(address = address, allowed_from_email = allowed_from_email, used_at__isnull = True)
    
    def create_new(self, post, user):
        reply_address = ReplyAddress(post = post, user = user, allowed_from_email = user.email)
        while True:
            reply_address.address = ''.join(random.choice(string.letters +
                string.digits) for i in xrange(random.randint(12, 25))).lower()
            if self.filter(address = reply_address.address).count() == 0:
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

    def create_reply(self, content, attachments = None):
        result = None

        if attachments:
            #cheap way of dealing with the attachments
            #just insert them inline, however it might
            #be useful to keep track of the uploaded files separately
            #and deal with them as with resources of their own value
            for att in attachments:
                file_storage, file_name, file_url = store_file(att)
                result += '[%s](%s) ' % (att.name, file_url)

        if self.post.post_type == 'answer':
            result = self.user.post_comment(self.post, content)
        elif self.post.post_type == 'question':
            wordcount = len(content)/6#this is a simplistic hack
            if wordcount > askbot_settings.MIN_WORDS_FOR_ANSWER_BY_EMAIL:
                result = self.user.post_answer(self.post, content)
            else:
                result = self.user.post_comment(self.post, content)
        elif self.post.post_type == 'comment':
            result = self.user.post_comment(self.post.parent, content)
        result.thread.invalidate_cached_data()
        self.used_at = datetime.now()
        self.save()
        return result




