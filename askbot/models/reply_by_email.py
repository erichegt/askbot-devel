from datetime import datetime
import random
import string
import os
from django.db import models
from django.contrib.auth.models import User
from askbot.models.post import Post
from askbot.models.base import BaseQuerySetManager
from askbot.utils.file_utils import store_file
from askbot.conf import settings as askbot_settings
from django.utils.translation import ugettext_lazy as _

def process_attachments(attachments):
    """saves file attachments and adds
    
    cheap way of dealing with the attachments
    just insert them inline, however it might
    be useful to keep track of the uploaded files separately
    and deal with them as with resources of their own value"""
    if attachments:
        content = ''
        for att in attachments:
            file_storage, file_name, file_url = store_file(att)
            chunk = '[%s](%s) ' % (att.name, file_url)
            file_extension = os.path.splitext(att.name)
            #todo: this is a hack - use content type
            if file_extension.lower() in ('png', 'jpg', 'gif'):
                chunk = '\n\n!' + chunk
            content += '\n\n' + chunk
        return content
    else:
        return ''

class ReplyAddressManager(BaseQuerySetManager):

    def get_unused(self, address, allowed_from_email):
        return self.get(
            address = address,
            allowed_from_email = allowed_from_email,
            used_at__isnull = True
        )
    
    def create_new(self, post, user):
        reply_address = ReplyAddress(
            post = post,
            user = user,
            allowed_from_email = user.email
        )
        while True:
            reply_address.address = ''.join(random.choice(string.letters +
                string.digits) for i in xrange(random.randint(12, 25))).lower()
            if self.filter(address = reply_address.address).count() == 0:
                break
        reply_address.save()
        return reply_address
			

class ReplyAddress(models.Model):
    address = models.CharField(max_length = 25, unique = True)
    post = models.ForeignKey(
                            Post,
                            related_name = 'reply_addresses'
                        )#the emailed post
    response_post = models.ForeignKey(
                            Post,
                            null = True,
                            related_name = 'edit_addresses'
                        )
    user = models.ForeignKey(User)
    allowed_from_email = models.EmailField(max_length = 150)
    used_at = models.DateTimeField(null = True, default = None)

    objects = ReplyAddressManager()


    class Meta:
        app_label = 'askbot'
        db_table = 'askbot_replyaddress'

    @property
    def was_used(self):
        """True if was used"""
        return self.used_at != None

    def edit_post(self, content, attachments = None):
        """edits the created post upon repeated response
        to the same address"""
        assert self.was_used == True
        content += process_attachments(attachments)
        self.user.edit_post(
            post = self.response_post,
            body_text = content,
            revision_comment = _('edited by email')
        )
        self.response_post.thread.invalidate_cached_data()

    def create_reply(self, content, attachments = None):
        """creates a reply to the post which was emailed
        to the user
        """
        result = None
        content += process_attachments(attachments)

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
        self.response_post = result
        self.used_at = datetime.now()
        self.save()
        return result




