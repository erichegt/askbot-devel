from question import Question ,QuestionRevision, QuestionView, AnonymousQuestion, FavoriteQuestion
from answer import Answer, AnonymousAnswer, AnswerRevision
from tag import Tag, MarkedTag
from meta import Vote, Comment, FlaggedItem
from user import Activity, AnonymousEmail, EmailFeedSetting, AuthKeyUserAssociation
from repute import Badge, Award, Repute

from base import *

# User extend properties
QUESTIONS_PER_PAGE_CHOICES = (
   (10, u'10'),
   (30, u'30'),
   (50, u'50'),
)

def user_is_username_taken(cls,username):
    try:
        cls.objects.get(username=username)
        return True
    except cls.MultipleObjectsReturned:
        return True
    except cls.DoesNotExist:
        return False

def user_get_q_sel_email_feed_frequency(self):
    #print 'looking for frequency for user %s' % self
    try:
        feed_setting = EmailFeedSetting.objects.get(subscriber=self,feed_type='q_sel')
    except Exception, e:
        #print 'have error %s' % e.message
        raise e
    #print 'have freq=%s' % feed_setting.frequency
    return feed_setting.frequency

User.add_to_class('is_approved', models.BooleanField(default=False))
User.add_to_class('email_isvalid', models.BooleanField(default=False))
User.add_to_class('email_key', models.CharField(max_length=32, null=True))
User.add_to_class('reputation', models.PositiveIntegerField(default=1))
User.add_to_class('gravatar', models.CharField(max_length=32))

#User.add_to_class('favorite_questions',
#                  models.ManyToManyField(Question, through=FavoriteQuestion,
#                                         related_name='favorited_by'))

#User.add_to_class('badges', models.ManyToManyField(Badge, through=Award,
#                                                   related_name='awarded_to'))
User.add_to_class('gold', models.SmallIntegerField(default=0))
User.add_to_class('silver', models.SmallIntegerField(default=0))
User.add_to_class('bronze', models.SmallIntegerField(default=0))
User.add_to_class('questions_per_page',
                  models.SmallIntegerField(choices=QUESTIONS_PER_PAGE_CHOICES, default=10))
User.add_to_class('last_seen',
                  models.DateTimeField(default=datetime.datetime.now))
User.add_to_class('real_name', models.CharField(max_length=100, blank=True))
User.add_to_class('website', models.URLField(max_length=200, blank=True))
User.add_to_class('location', models.CharField(max_length=100, blank=True))
User.add_to_class('date_of_birth', models.DateField(null=True, blank=True))
User.add_to_class('about', models.TextField(blank=True))
User.add_to_class('is_username_taken',classmethod(user_is_username_taken))
User.add_to_class('get_q_sel_email_feed_frequency',user_get_q_sel_email_feed_frequency)
User.add_to_class('hide_ignored_questions', models.BooleanField(default=False))
User.add_to_class('tag_filter_setting',
                    models.CharField(
                                        max_length=16,
                                        choices=TAG_EMAIL_FILTER_CHOICES,
                                        default='ignored'
                                     )
                 )

# custom signal
tags_updated = django.dispatch.Signal(providing_args=["question"])
edit_question_or_answer = django.dispatch.Signal(providing_args=["instance", "modified_by"])
delete_post_or_answer = django.dispatch.Signal(providing_args=["instance", "deleted_by"])
mark_offensive = django.dispatch.Signal(providing_args=["instance", "mark_by"])
user_updated = django.dispatch.Signal(providing_args=["instance", "updated_by"])
user_logged_in = django.dispatch.Signal(providing_args=["session"])


def get_messages(self):
    messages = []
    for m in self.message_set.all():
        messages.append(m.message)
    return messages

def delete_messages(self):
    self.message_set.all().delete()

def get_profile_url(self):
    """Returns the URL for this User's profile."""
    return '%s%s/' % (reverse('user', args=[self.id]), slugify(self.username))

def get_profile_link(self):
    profile_link = u'<a href="%s">%s</a>' % (self.get_profile_url(),self.username)
    logging.debug('in get profile link %s' % profile_link)
    return mark_safe(profile_link)

User.add_to_class('get_profile_url', get_profile_url)
User.add_to_class('get_profile_link', get_profile_link)
User.add_to_class('get_messages', get_messages)
User.add_to_class('delete_messages', delete_messages)

def calculate_gravatar_hash(instance, **kwargs):
    """Calculates a User's gravatar hash from their email address."""
    if kwargs.get('raw', False):
        return
    instance.gravatar = hashlib.md5(instance.email).hexdigest()

def record_ask_event(instance, created, **kwargs):
    if created:
        activity = Activity(user=instance.author, active_at=instance.added_at, content_object=instance, activity_type=TYPE_ACTIVITY_ASK_QUESTION)
        activity.save()

def record_answer_event(instance, created, **kwargs):
    if created:
        activity = Activity(user=instance.author, active_at=instance.added_at, content_object=instance, activity_type=TYPE_ACTIVITY_ANSWER)
        activity.save()

def record_comment_event(instance, created, **kwargs):
    if created:
        from django.contrib.contenttypes.models import ContentType
        question_type = ContentType.objects.get_for_model(Question)
        question_type_id = question_type.id
        if (instance.content_type_id == question_type_id):
            type = TYPE_ACTIVITY_COMMENT_QUESTION
        else:
            type = TYPE_ACTIVITY_COMMENT_ANSWER
        activity = Activity(user=instance.user, active_at=instance.added_at, content_object=instance, activity_type=type)
        activity.save()

def record_revision_question_event(instance, created, **kwargs):
    if created and instance.revision <> 1:
        activity = Activity(user=instance.author, active_at=instance.revised_at, content_object=instance, activity_type=TYPE_ACTIVITY_UPDATE_QUESTION)
        activity.save()

def record_revision_answer_event(instance, created, **kwargs):
    if created and instance.revision <> 1:
        activity = Activity(user=instance.author, active_at=instance.revised_at, content_object=instance, activity_type=TYPE_ACTIVITY_UPDATE_ANSWER)
        activity.save()

def record_award_event(instance, created, **kwargs):
    """
    After we awarded a badge to user, we need to record this activity and notify user.
    We also recaculate awarded_count of this badge and user information.
    """
    if created:
        activity = Activity(user=instance.user, active_at=instance.awarded_at, content_object=instance,
            activity_type=TYPE_ACTIVITY_PRIZE)
        activity.save()

        instance.badge.awarded_count += 1
        instance.badge.save()

        if instance.badge.type == Badge.GOLD:
            instance.user.gold += 1
        if instance.badge.type == Badge.SILVER:
            instance.user.silver += 1
        if instance.badge.type == Badge.BRONZE:
            instance.user.bronze += 1
        instance.user.save()

def notify_award_message(instance, created, **kwargs):
    """
    Notify users when they have been awarded badges by using Django message.
    """
    if created:
        user = instance.user
        user.message_set.create(message=u"Congratulations, you have received a badge '%s'" % instance.badge.name)

def record_answer_accepted(instance, created, **kwargs):
    """
    when answer is accepted, we record this for question author - who accepted it.
    """
    if not created and instance.accepted:
        activity = Activity(user=instance.question.author, active_at=datetime.datetime.now(), \
            content_object=instance, activity_type=TYPE_ACTIVITY_MARK_ANSWER)
        activity.save()

def update_last_seen(instance, created, **kwargs):
    """
    when user has activities, we update 'last_seen' time stamp for him
    """
    user = instance.user
    user.last_seen = datetime.datetime.now()
    user.save()

def record_vote(instance, created, **kwargs):
    """
    when user have voted
    """
    if created:
        if instance.vote == 1:
            vote_type = TYPE_ACTIVITY_VOTE_UP
        else:
            vote_type = TYPE_ACTIVITY_VOTE_DOWN

        activity = Activity(user=instance.user, active_at=instance.voted_at, content_object=instance, activity_type=vote_type)
        activity.save()

def record_cancel_vote(instance, **kwargs):
    """
    when user canceled vote, the vote will be deleted.
    """
    activity = Activity(user=instance.user, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_CANCEL_VOTE)
    activity.save()

def record_delete_question(instance, delete_by, **kwargs):
    """
    when user deleted the question
    """
    if instance.__class__ == "Question":
        activity_type = TYPE_ACTIVITY_DELETE_QUESTION
    else:
        activity_type = TYPE_ACTIVITY_DELETE_ANSWER

    activity = Activity(user=delete_by, active_at=datetime.datetime.now(), content_object=instance, activity_type=activity_type)
    activity.save()

def record_mark_offensive(instance, mark_by, **kwargs):
    activity = Activity(user=mark_by, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_MARK_OFFENSIVE)
    activity.save()

def record_update_tags(question, **kwargs):
    """
    when user updated tags of the question
    """
    activity = Activity(user=question.author, active_at=datetime.datetime.now(), content_object=question, activity_type=TYPE_ACTIVITY_UPDATE_TAGS)
    activity.save()

def record_favorite_question(instance, created, **kwargs):
    """
    when user add the question in him favorite questions list.
    """
    if created:
        activity = Activity(user=instance.user, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_FAVORITE)
        activity.save()

def record_user_full_updated(instance, **kwargs):
    activity = Activity(user=instance, active_at=datetime.datetime.now(), content_object=instance, activity_type=TYPE_ACTIVITY_USER_FULL_UPDATED)
    activity.save()

def post_stored_anonymous_content(sender,user,session_key,signal,*args,**kwargs):
    aq_list = AnonymousQuestion.objects.filter(session_key = session_key)
    aa_list = AnonymousAnswer.objects.filter(session_key = session_key)
    import settings
    if settings.EMAIL_VALIDATION == 'on':#add user to the record
        for aq in aq_list:
            aq.author = user
            aq.save()
        for aa in aa_list:
            aa.author = user
            aa.save()
        #maybe add pending posts message?
    else: #just publish the questions
        for aq in aq_list:
            aq.publish(user)
        for aa in aa_list:
            aa.publish(user)

#signal for User modle save changes

pre_save.connect(calculate_gravatar_hash, sender=User)
post_save.connect(record_ask_event, sender=Question)
post_save.connect(record_answer_event, sender=Answer)
post_save.connect(record_comment_event, sender=Comment)
post_save.connect(record_revision_question_event, sender=QuestionRevision)
post_save.connect(record_revision_answer_event, sender=AnswerRevision)
post_save.connect(record_award_event, sender=Award)
post_save.connect(notify_award_message, sender=Award)
post_save.connect(record_answer_accepted, sender=Answer)
post_save.connect(update_last_seen, sender=Activity)
post_save.connect(record_vote, sender=Vote)
post_delete.connect(record_cancel_vote, sender=Vote)
delete_post_or_answer.connect(record_delete_question, sender=Question)
delete_post_or_answer.connect(record_delete_question, sender=Answer)
mark_offensive.connect(record_mark_offensive, sender=Question)
mark_offensive.connect(record_mark_offensive, sender=Answer)
tags_updated.connect(record_update_tags, sender=Question)
post_save.connect(record_favorite_question, sender=FavoriteQuestion)
user_updated.connect(record_user_full_updated, sender=User)
user_logged_in.connect(post_stored_anonymous_content)

Question = Question
QuestionRevision = QuestionRevision
QuestionView = QuestionView
FavoriteQuestion = FavoriteQuestion
AnonymousQuestion = AnonymousQuestion

Answer = Answer
AnswerRevision = AnswerRevision
AnonymousAnswer = AnonymousAnswer

Tag = Tag
Comment = Comment
Vote = Vote
FlaggedItem = FlaggedItem
MarkedTag = MarkedTag

Badge = Badge
Award = Award
Repute = Repute

Activity = Activity
EmailFeedSetting = EmailFeedSetting
AnonymousEmail = AnonymousEmail
AuthKeyUserAssociation = AuthKeyUserAssociation

__all__ = [
        'Question',
        'QuestionRevision',
        'QuestionView',
        'FavoriteQuestion',
        'AnonymousQuestion',

        'Answer',
        'AnswerRevision',
        'AnonymousAnswer',

        'Tag',
        'Comment',
        'Vote',
        'FlaggedItem',
        'MarkedTag',

        'Badge',
        'Award',
        'Repute',

        'Activity',
        'EmailFeedSetting',
        'AnonymousEmail',
        'AuthKeyUserAssociation',

        'User'
        ]


from forum.modules import get_modules_script_classes

for k, v in get_modules_script_classes('models', models.Model).items():
    if not k in __all__:
        __all__.append(k)
        exec "%s = v" % k