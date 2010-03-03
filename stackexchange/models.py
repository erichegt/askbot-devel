from django.db import models
class StackExchangeBadge(models.Model):
    class_type = models.IntegerField()
    name = models.CharField(max_length=50)
    description = models.TextField()
    single = models.BooleanField()
    secret = models.BooleanField()
    tag_based = models.BooleanField()
    command = models.TextField()
    award_frequency = models.IntegerField()

class StackExchangeCloseReason(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=256)
    display_order = models.IntegerField()

class StackExchangeComment2Vote(models.Model):
    post_comment = models.ForeignKey('StackExchangePostComment', related_name='StackExchangeComment2Vote_post_comment_set', null=True)
    vote_type = models.ForeignKey('StackExchangeVoteType', related_name='StackExchangeComment2Vote_vote_type_set', null=True)
    creation_date = models.DateTimeField()
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeComment2Vote_user_set', null=True)
    ip_address = models.CharField(max_length=40)
    user_display_name = models.CharField(max_length=40)
    deletion_date = models.DateTimeField()

class StackExchangeFlatPage(models.Model):
    name = models.CharField(max_length=50)
    url = models.CharField(max_length=128)
    value = models.TextField()
    content_type = models.CharField(max_length=50)
    active = models.BooleanField()
    use_master = models.BooleanField()

class StackExchangeMessage(models.Model):
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeMessage_user_set', null=True)
    message_type = models.ForeignKey('StackExchangeMessageType', related_name='StackExchangeMessage_message_type_set', null=True)
    is_read = models.BooleanField()
    creation_date = models.DateTimeField()
    text = models.TextField()
    post = models.ForeignKey('StackExchangePost', related_name='StackExchangeMessage_post_set', null=True)

class StackExchangeMessageType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

class StackExchangeModeratorMessage(models.Model):
    message_type = models.ForeignKey('StackExchangeMessageType', related_name='StackExchangeModeratorMessage_message_type_set', null=True)
    creation_date = models.DateTimeField()
    creation_ip_address = models.CharField(max_length=40)
    text = models.TextField()
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeModeratorMessage_user_set', null=True)
    post = models.ForeignKey('StackExchangePost', related_name='StackExchangeModeratorMessage_post_set', null=True)
    deletion_date = models.DateTimeField()
    deletion_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeModeratorMessage_deletion_user_set', null=True)
    deletion_ip_address = models.CharField(max_length=40)
    user_display_name = models.CharField(max_length=40)

class StackExchangePostComment(models.Model):
    post = models.ForeignKey('StackExchangePost', related_name='StackExchangePostComment_post_set', null=True)
    text = models.TextField()
    creation_date = models.DateTimeField()
    ip_address = models.CharField(max_length=15)
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePostComment_user_set', null=True)
    user_display_name = models.CharField(max_length=30)
    deletion_date = models.DateTimeField()
    deletion_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePostComment_deletion_user_set', null=True)
    score = models.IntegerField()

class StackExchangePostHistoryType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

class StackExchangePostHistory(models.Model):
    post_history_type = models.ForeignKey('StackExchangePostHistoryType', related_name='StackExchangePostHistory_post_history_type_set', null=True)
    post = models.ForeignKey('StackExchangePost', related_name='StackExchangePostHistory_post_set', null=True)
    revision_guid = models.CharField(max_length=64)
    creation_date = models.DateTimeField()
    ip_address = models.CharField(max_length=40)
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePostHistory_user_set', null=True)
    comment = models.CharField(max_length=400)
    text = models.TextField()
    user_display_name = models.CharField(max_length=40)
    user_email = models.CharField(max_length=100)
    user_website_url = models.CharField(max_length=200)

class StackExchangePost2Vote(models.Model):
    post = models.ForeignKey('StackExchangePost', related_name='StackExchangePost2Vote_post_set', null=True)
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePost2Vote_user_set', null=True)
    vote_type = models.ForeignKey('StackExchangeVoteType', related_name='StackExchangePost2Vote_vote_type_set', null=True)
    creation_date = models.DateTimeField()
    deletion_date = models.DateTimeField()
    target_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePost2Vote_target_user_set', null=True)
    target_rep_change = models.IntegerField()
    voter_rep_change = models.IntegerField()
    comment = models.CharField(max_length=150)
    ip_address = models.CharField(max_length=40)
    linked_post = models.ForeignKey('StackExchangePost', related_name='StackExchangePost2Vote_linked_post_set', null=True)

class StackExchangePost(models.Model):
    post_type = models.ForeignKey('StackExchangePostType', related_name='StackExchangePost_post_type_set', null=True)
    creation_date = models.DateTimeField()
    score = models.IntegerField()
    view_count = models.IntegerField()
    body = models.TextField()
    owner_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePost_owner_user_set', null=True)
    last_editor_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePost_last_editor_user_set', null=True)
    last_edit_date = models.DateTimeField()
    last_activity_date = models.DateTimeField()
    last_activity_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangePost_last_activity_user_set', null=True)
    parent = models.ForeignKey('self', related_name='StackExchangePost_parent_set', null=True)
    accepted_answer = models.ForeignKey('self', related_name='StackExchangePost_accepted_answer_set', null=True)
    title = models.CharField(max_length=250)
    tags = models.CharField(max_length=150)
    community_owned_date = models.DateTimeField()
    history_summary = models.CharField(max_length=150)
    answer_score = models.IntegerField()
    answer_count = models.IntegerField()
    comment_count = models.IntegerField()
    favorite_count = models.IntegerField()
    deletion_date = models.DateTimeField()
    closed_date = models.DateTimeField()
    locked_date = models.DateTimeField()
    locked_duration = models.IntegerField()
    owner_display_name = models.CharField(max_length=40)
    last_editor_display_name = models.CharField(max_length=40)
    bounty_amount = models.IntegerField()
    bounty_closes = models.DateTimeField()
    bounty_closed = models.DateTimeField()
    last_owner_email_date = models.DateTimeField()

class StackExchangePostType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

class StackExchangeSchemaVersion(models.Model):
    version = models.IntegerField()

class StackExchangeSetting(models.Model):
    key = models.CharField(max_length=256)
    value = models.TextField()

class StackExchangeSystemMessage(models.Model):
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeSystemMessage_user_set', null=True)
    creation_date = models.DateTimeField()
    text = models.TextField()
    deletion_date = models.DateTimeField()
    deletion_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeSystemMessage_deletion_user_set', null=True)

class StackExchangeTag(models.Model):
    name = models.CharField(max_length=50)
    count = models.IntegerField()
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeTag_user_set', null=True)
    creation_date = models.DateTimeField()
    is_moderator_only = models.BooleanField()
    is_required = models.BooleanField()
    aliases = models.CharField(max_length=200)

class StackExchangeThemeResource(models.Model):
    name = models.CharField(max_length=50)
    value = models.TextField()
    content_type = models.CharField(max_length=50)
    version = models.CharField(max_length=6)

class StackExchangeThemeTextResource(models.Model):
    name = models.CharField(max_length=50)
    value = models.TextField()
    content_type = models.CharField(max_length=50)

class StackExchangeThrottleBucket(models.Model):
    type = models.CharField(max_length=256)
    ip_address = models.CharField(max_length=64)
    tokens = models.IntegerField()
    last_update = models.DateTimeField()

class StackExchangeUserHistoryType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

class StackExchangeUserHistory(models.Model):
    user_history_type = models.ForeignKey('StackExchangeUserHistoryType', related_name='StackExchangeUserHistory_user_history_type_set', null=True)
    creation_date = models.DateTimeField()
    ip_address = models.CharField(max_length=40)
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeUserHistory_user_set', null=True)
    comment = models.CharField(max_length=400)
    user_display_name = models.CharField(max_length=40)
    moderator_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeUserHistory_moderator_user_set', null=True)
    reputation = models.IntegerField()

class StackExchangeUser2Badge(models.Model):
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeUser2Badge_user_set', null=True)
    badge = models.ForeignKey('StackExchangeBadge', related_name='StackExchangeUser2Badge_badge_set', null=True)
    date = models.DateTimeField()
    comment = models.CharField(max_length=50)

class StackExchangeUser2Vote(models.Model):
    user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeUser2Vote_user_set', null=True)
    vote_type = models.ForeignKey('StackExchangeVoteType', related_name='StackExchangeUser2Vote_vote_type_set', null=True)
    target_user = models.ForeignKey('StackExchangeUser', related_name='StackExchangeUser2Vote_target_user_set', null=True)
    creation_date = models.DateTimeField()
    deletion_date = models.DateTimeField()
    ip_address = models.CharField(max_length=40)

class StackExchangeUser(models.Model):
    user_type = models.ForeignKey('StackExchangeUserType', related_name='StackExchangeUser_user_type_set', null=True)
    open_id = models.CharField(max_length=200)
    reputation = models.IntegerField()
    views = models.IntegerField()
    creation_date = models.DateTimeField()
    last_access_date = models.DateTimeField()
    has_replies = models.BooleanField()
    has_message = models.BooleanField()
    opt_in_email = models.BooleanField()
    opt_in_recruit = models.BooleanField()
    last_login_date = models.DateTimeField()
    last_email_date = models.DateTimeField()
    last_login_ip = models.CharField(max_length=15)
    open_id_alt = models.CharField(max_length=200)
    email = models.CharField(max_length=100)
    display_name = models.CharField(max_length=40)
    display_name_cleaned = models.CharField(max_length=40)
    website_url = models.CharField(max_length=200)
    real_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    birthday = models.DateTimeField()
    badge_summary = models.CharField(max_length=50)
    about_me = models.TextField()
    preferences_raw = models.TextField()
    timed_penalty_date = models.DateTimeField()
    guid = models.CharField(max_length=64)
    phone = models.CharField(max_length=20)
    password_id = models.IntegerField()

class StackExchangeUserType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

class StackExchangeVoteType(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=300)

