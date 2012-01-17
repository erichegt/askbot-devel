from datetime import datetime
import random
import string

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from askbot.models.post import Post
from askbot.models.base import BaseQuerySetManager
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

    def create_reply(self, content):
        result = None
        if self.post.post_type == 'answer' or self.post.post_type == 'comment':
            result = self.user.post_comment(self.post, content)
        elif self.post.post_type == 'question':
            wordcount = len(content.rsplit())
            if wordcount > askbot_settings.MIN_WORDS_FOR_ANSWER_BY_EMAIL:
                result = self.user.post_answer(self.post, content)
            else:
                result = self.user.post_comment(self.post, content)
        self.used_at = datetime.now()
        self.save()
        return result


#TODO move this function to a more appropriate module
def process_reply_email(message, address, host):

    error = None
    try:
        reply_address = ReplyAddress.objects.get_unused(address, message.From)
        separator = _("======= Reply above this line. ====-=-=")
        parts = message.body().split(separator)
        if len(parts) != 2 :
            error = _("Your message was malformed. Please make sure to qoute \
                the original notification you received at the end of your reply.")
        else:
            reply_part = parts[0]
            reply_address.create_reply(reply_part.strip())
    except ReplyAddress.DoesNotExist:
        error = _("You were replying to an email address\
         unknown to the system or you were replying from a different address from the one where you\
         received the notification.")
    if error is not None:
        from askbot.utils import mail
        from django.template import Context
        from askbot.skins.loaders import get_template

        template = get_template('reply_by_email_error.html')
        body_text = template.render(Context({'error':error}))
        mail.send_mail(
            subject_line = "Error posting your reply",
            body_text = body_text,
            recipient_list = [message.From],
        )        


