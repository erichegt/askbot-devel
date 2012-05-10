from datetime import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.models.post import Post
from askbot.models.base import BaseQuerySetManager
from askbot.conf import settings as askbot_settings
from askbot.utils import mail

class ReplyAddressManager(BaseQuerySetManager):
    """A manager for the :class:`ReplyAddress` model"""

    def get_unused(self, address, allowed_from_email):
        return self.get(
            address = address,
            allowed_from_email = allowed_from_email,
            used_at__isnull = True
        )
    
    def create_new(self, post, user):
        """creates a new reply address"""
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
    """Stores a reply address for the post
    and the user"""
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

    def edit_post(self, parts):
        """edits the created post upon repeated response
        to the same address"""
        assert self.was_used == True
        content, stored_files = mail.process_parts(parts)
        self.user.edit_post(
            post = self.response_post,
            body_text = content,
            revision_comment = _('edited by email'),
            by_email = True
        )
        self.response_post.thread.invalidate_cached_data()

    def create_reply(self, parts):
        """creates a reply to the post which was emailed
        to the user
        """
        result = None
        #todo: delete stored files if this function fails
        content, stored_files = mail.process_parts(parts)

        if self.post.post_type == 'answer':
            result = self.user.post_comment(
                                        self.post,
                                        content,
                                        by_email = True
                                    )
        elif self.post.post_type == 'question':
            wordcount = len(content)/6#this is a simplistic hack
            if wordcount > askbot_settings.MIN_WORDS_FOR_ANSWER_BY_EMAIL:
                result = self.user.post_answer(
                                            self.post,
                                            content,
                                            by_email = True
                                        )
            else:
                result = self.user.post_comment(
                                            self.post,
                                            content,
                                            by_email = True
                                        )
        elif self.post.post_type == 'comment':
            result = self.user.post_comment(
                                    self.post.parent,
                                    content,
                                    by_email = True
                                )
        result.thread.invalidate_cached_data()
        self.response_post = result
        self.used_at = datetime.now()
        self.save()
        return result
