import re
from django.db import models
from django.contrib.auth.models import User as DjangoUser
from django.utils.html import strip_tags
from askbot.utils.html import unescape

TAGS = {}#internal cache for mappings forum id -> forum name

class Post(models.Model):
    body = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    entry_id = models.IntegerField()
    post_id = models.IntegerField()
    forum_id = models.IntegerField()
    user_id = models.IntegerField()
    is_informative = models.BooleanField()
    is_processed = models.BooleanField(default = False)

    def get_author(self):
        """returns author of the post, from the Django user table"""
        zendesk_user = User.objects.get(user_id = self.user_id)
        return DjangoUser.objects.get(id = zendesk_user.askbot_user_id)

    def get_body_text(self):
        """unescapes html entities in the body text,
        saves in the internal cache and returns the value"""
        if not hasattr(self, '_body_text'):
            self._body_text = unescape(self.body)
        return self._body_text

    def get_fake_title(self):
        """extract first 10 words from the body text and strip tags"""
        words = re.split(r'\s+', self.get_body_text())
        if len(words) > 10:
            words = words[:10]
        return strip_tags(' '.join(words))

    def get_tag_name(self):
        if self.forum_id not in TAGS:
            forum = Forum.objects.get(forum_id = self.forum_id)
            tag_name = re.sub(r'\s+', '-', forum.name.lower())
            TAGS[self.forum_id] = tag_name
        return TAGS[self.forum_id]

class User(models.Model):
    user_id = models.IntegerField()
    askbot_user_id = models.IntegerField(null = True)
    created_at = models.DateTimeField()
    is_active = models.BooleanField()
    last_login = models.DateTimeField(null = True)
    name = models.CharField(max_length = 255)
    openid_url = models.URLField(null = True)
    organization_id = models.IntegerField(null = True)
    phone = models.CharField(max_length = 32, null = True)
    restriction_id = models.IntegerField()
    roles = models.IntegerField()
    time_zone = models.CharField(max_length = 255)
    updated_at = models.DateTimeField()
    uses_12_hour_clock = models.BooleanField()
    email = models.EmailField(null = True)
    is_verified = models.BooleanField()
    photo_url = models.URLField()

class Forum(models.Model):
    description = models.CharField(max_length = 255, null = True)
    display_type_id = models.IntegerField()
    entries_count = models.IntegerField()
    forum_id = models.IntegerField()
    is_locked = models.BooleanField()
    name = models.CharField(max_length = 255)
    organization_id = models.IntegerField(null = True)
    position = models.IntegerField(null = True)
    updated_at = models.DateTimeField()
    translation_locale_id = models.IntegerField(null = True)
    use_for_suggestions = models.BooleanField()
    visibility_restriction_id = models.IntegerField()
    is_public = models.BooleanField()
