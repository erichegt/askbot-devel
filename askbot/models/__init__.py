import logging
import re
import hashlib
import datetime
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from askbot.search.indexer import create_fulltext_indexes
from django.db.models import signals as django_signals
from django.template import loader, Context
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.db import models
from django.conf import settings as django_settings
from django.contrib.contenttypes.models import ContentType
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.models.question import Question, QuestionRevision
from askbot.models.question import QuestionView, AnonymousQuestion
from askbot.models.question import FavoriteQuestion
from askbot.models.answer import Answer, AnonymousAnswer, AnswerRevision
from askbot.models.tag import Tag, MarkedTag
from askbot.models.meta import Vote, Comment, FlaggedItem
from askbot.models.user import Activity, ValidationHash, EmailFeedSetting
from askbot.models import signals
#from user import AuthKeyUserAssociation
from askbot.models.repute import Badge, Award, Repute
from askbot import auth

User.add_to_class('is_approved', models.BooleanField(default=False))
User.add_to_class('email_isvalid', models.BooleanField(default=False))
User.add_to_class('email_key', models.CharField(max_length=32, null=True))
#hardcoded initial reputaion of 1, no setting for this one
User.add_to_class('reputation', models.PositiveIntegerField(default=1))
User.add_to_class('gravatar', models.CharField(max_length=32))
User.add_to_class('gold', models.SmallIntegerField(default=0))
User.add_to_class('silver', models.SmallIntegerField(default=0))
User.add_to_class('bronze', models.SmallIntegerField(default=0))
User.add_to_class('questions_per_page',
                  models.SmallIntegerField(
                                choices=const.QUESTIONS_PER_PAGE_USER_CHOICES,
                                default=10)
                            )
User.add_to_class('last_seen',
                  models.DateTimeField(default=datetime.datetime.now))
User.add_to_class('real_name', models.CharField(max_length=100, blank=True))
User.add_to_class('website', models.URLField(max_length=200, blank=True))
User.add_to_class('location', models.CharField(max_length=100, blank=True))
User.add_to_class('date_of_birth', models.DateField(null=True, blank=True))
User.add_to_class('about', models.TextField(blank=True))
User.add_to_class('hide_ignored_questions', models.BooleanField(default=False))
User.add_to_class('tag_filter_setting',
                    models.CharField(
                                        max_length=16,
                                        choices=const.TAG_EMAIL_FILTER_CHOICES,
                                        default='ignored'
                                     )
                 )
User.add_to_class('response_count', models.IntegerField(default=0))

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
        feed_setting = EmailFeedSetting.objects.get(
                                        subscriber=self,
                                        feed_type='q_sel'
                                    )
    except Exception, e:
        #print 'have error %s' % e.message
        raise e
    #print 'have freq=%s' % feed_setting.frequency
    return feed_setting.frequency

def get_messages(self):
    messages = []
    for m in self.message_set.all():
        messages.append(m.message)
    return messages

def delete_messages(self):
    self.message_set.all().delete()

#todo: find where this is used and replace with get_absolute_url
def get_profile_url(self):
    """Returns the URL for this User's profile."""
    return reverse(
                'user_profile', 
                kwargs={'id':self.id, 'slug':slugify(self.username)}
            )

def user_get_absolute_url(self):
    return self.get_profile_url()

def get_profile_link(self):
    profile_link = u'<a href="%s">%s</a>' \
        % (self.get_profile_url(),self.username)

    return mark_safe(profile_link)

#series of methods for user vote-type commands
#same call signature func(self, post, timestamp=None, cancel=None)
#note that none of these have business logic checks internally
#these functions are used by the askbot app and
#by the data importer jobs from say stackexchange, where internal rules
#may be different
#maybe if we do use business rule checks here - we should add
#some flag allowing to bypass them for things like the data importers
def toggle_favorite_question(self, question, timestamp=None, cancel=False):
    """cancel has no effect here, but is important for the SE loader
    it is hoped that toggle will work and data will be consistent
    but there is no guarantee, maybe it's better to be more strict 
    about processing the "cancel" option
    another strange thing is that this function unlike others below
    returns a value
    """
    try:
        fave = FavoriteQuestion.objects.get(question=question, user=self)
        fave.delete()
        result = False
    except FavoriteQuestion.DoesNotExist:
        if timestamp is None:
            timestamp = datetime.datetime.now()
        fave = FavoriteQuestion(
            question = question,
            user = self,
            added_at = timestamp,
        )
        fave.save()
        result = True
    Question.objects.update_favorite_count(question)
    return result

def _process_vote(user, post, timestamp=None, cancel=False, vote_type=None):
    """"private" wrapper function that applies post upvotes/downvotes
    and cancelations
    """
    post_type = ContentType.objects.get_for_model(post)
    #get or create the vote object
    #return with noop in some situations
    try:
        vote = Vote.objects.get(
                    user = user,
                    content_type = post_type,
                    object_id = post.id,
                )
    except Vote.DoesNotExist:
        vote = None
    if cancel:
        if vote == None:
            return
        elif vote.is_opposite(vote_type):
            return
        else:
            #we would call vote.delete() here
            #but for now all that is handled by the
            #legacy askbot.auth functions
            #vote.delete()
            pass
    else:
        if vote == None:
            vote = Vote(
                    user = user,
                    content_object = post,
                    vote = vote_type,
                    voted_at = timestamp,
                    )
        elif vote.is_opposite(vote_type):
            vote.vote = vote_type
        else:
            return

    #do the actual work
    if vote_type == Vote.VOTE_UP:
        if cancel:
            auth.onUpVotedCanceled(vote, post, user, timestamp)
        else:
            auth.onUpVoted(vote, post, user, timestamp)
    elif vote_type == Vote.VOTE_DOWN:
        if cancel:
            auth.onDownVotedCanceled(vote, post, user, timestamp)
        else:
            auth.onDownVoted(vote, post, user, timestamp)

def upvote(self, post, timestamp=None, cancel=False):
    _process_vote(
        self,post,
        timestamp=timestamp,
        cancel=cancel,
        vote_type=Vote.VOTE_UP
    )

def downvote(self, post, timestamp=None, cancel=False):
    _process_vote(
        self,post,
        timestamp=timestamp,
        cancel=cancel,
        vote_type=Vote.VOTE_DOWN
    )

def accept_answer(self, answer, timestamp=None, cancel=False):
    if cancel:
        auth.onAnswerAcceptCanceled(answer, self, timestamp=timestamp)
    else:
        auth.onAnswerAccept(answer, self, timestamp=timestamp)

def flag_post(user, post, timestamp=None, cancel=False):
    if cancel:#todo: can't unflag?
        return
    if post.flagged_items.filter(user=user).count() > 0:
        return
    else:
        flag = FlaggedItem(
                user = user,
                content_object = post,
                flagged_at = timestamp,
            )
        auth.onFlaggedItem(flag, post, user, timestamp=timestamp)

User.add_to_class('is_username_taken',classmethod(user_is_username_taken))
User.add_to_class(
            'get_q_sel_email_feed_frequency',
            user_get_q_sel_email_feed_frequency
        )
User.add_to_class('get_absolute_url', user_get_absolute_url)
User.add_to_class('upvote', upvote)
User.add_to_class('downvote', downvote)
User.add_to_class('accept_answer', accept_answer)
User.add_to_class('flag_post', flag_post)
User.add_to_class('get_profile_url', get_profile_url)
User.add_to_class('get_profile_link', get_profile_link)
User.add_to_class('get_messages', get_messages)
User.add_to_class('delete_messages', delete_messages)
User.add_to_class('toggle_favorite_question', toggle_favorite_question)

#todo: move this to askbot/utils ??
def format_instant_notification_body(
                                        to_user = None,
                                        from_user = None,
                                        post = None,
                                        update_type = None,
                                        template = None,
                                    ):
    """
    returns text of the instant notification body
    that is built when post is updated
    only update_types in const.RESPONSE_ACTIVITY_TYPE_MAP_FOR_TEMPLATES
    are supported
    """

    site_url = askbot_settings.APP_URL
    origin_post = post.get_origin_post()
    #todo: create a better method to access "sub-urls" in user views
    user_subscriptions_url = site_url + to_user.get_absolute_url() + \
                            '?sort=email_subscriptions'

    if update_type == 'question_comment':
        assert(isinstance(post, Comment))
        assert(isinstance(post.content_object, Question))
    elif update_type == 'answer_comment':
        assert(isinstance(post, Comment))
        assert(isinstance(post.content_object, Answer))
    elif update_type in ('answer_update', 'new_answer'):
        assert(isinstance(post, Answer))
    elif update_type in ('question_update', 'new_question'):
        assert(isinstance(post, Question))

    update_data = {
        'update_author_name': from_user.username,
        'post_url': site_url + post.get_absolute_url(),
        'origin_post_title': origin_post.title,
        'user_subscriptions_url': user_subscriptions_url
    }
    return template.render(Context(update_data))

#todo: action
def send_instant_notifications_about_activity_in_post(
                                                update_activity = None,
                                                post = None,
                                                receiving_users = [],
                                            ):
    """
    function called when posts are updated
    newly mentioned users are carried through to reduce
    database hits
    """

    acceptable_types = const.RESPONSE_ACTIVITY_TYPES_FOR_INSTANT_NOTIFICATIONS

    if update_activity.activity_type not in acceptable_types:
        return

    template = loader.get_template('instant_notification.html')

    update_type_map = const.RESPONSE_ACTIVITY_TYPE_MAP_FOR_TEMPLATES
    update_type = update_type_map[update_activity.activity_type]

    for user in receiving_users:

            subject = _('email update message subject')
            text = format_instant_notification_body(
                            to_user = user,
                            from_user = update_activity.user,
                            post = post,
                            update_type = update_type,
                            template = template,
                        )
            #todo: this could be packaged as an "action" - a bundle
            #of executive function with the activity log recording
            msg = EmailMessage(
                        subject,
                        text,
                        django_settings.DEFAULT_FROM_EMAIL,
                        [user.email]
                    )
            #msg.send()
            #print text
            EMAIL_UPDATE_ACTIVITY = const.TYPE_ACTIVITY_EMAIL_UPDATE_SENT
            email_activity = Activity(
                                    user = user,
                                    content_object = post.get_origin_post(),
                                    activity_type = EMAIL_UPDATE_ACTIVITY
                                )
            email_activity.save()


#todo: move to utils
def calculate_gravatar_hash(instance, **kwargs):
    """Calculates a User's gravatar hash from their email address."""
    if kwargs.get('raw', False):
        return
    instance.gravatar = hashlib.md5(instance.email).hexdigest()


def record_post_update_activity(
        post,
        newly_mentioned_users = list(), 
        updated_by = None,
        timestamp = None,
        created = False,
        **kwargs
    ):
    """called upon signal askbot.models.signals.post_updated
    which is sent at the end of save() method in posts
    """
    assert(timestamp != None)
    assert(updated_by != None)

    #todo: take into account created == True case
    (activity_type, update_object) = post.get_updated_activity_data(created)

    update_activity = Activity(
                    user = updated_by,
                    active_at = timestamp, 
                    content_object = post, 
                    activity_type = activity_type
                )
    update_activity.save()

    #what users are included depends on the post type
    #for example for question - all Q&A contributors
    #are included, for comments only authors of comments and parent 
    #post are included
    receiving_users = post.get_response_receivers(
                                exclude_list = [updated_by, ]
                            )

    update_activity.receiving_users.add(*receiving_users)

    assert(updated_by not in receiving_users)

    for user in set(receiving_users) | set(newly_mentioned_users):
        user.response_count += 1
        user.save()

    #todo: weird thing is that only comments need the receiving_users
    #argument to this call
    notification_subscribers = post.get_instant_notification_subscribers(
                                    potential_subscribers = receiving_users,
                                    mentioned_users = newly_mentioned_users,
                                    exclude_list = [updated_by, ]
                                )

    send_instant_notifications_about_activity_in_post(
                            update_activity = update_activity,
                            post = post,
                            receiving_users = notification_subscribers,
                        )


def record_award_event(instance, created, **kwargs):
    """
    After we awarded a badge to user, we need to 
    record this activity and notify user.
    We also recaculate awarded_count of this badge and user information.
    """
    if created:
        #todo: change this to community user who gives the award
        activity = Activity(
                        user=instance.user,
                        active_at=instance.awarded_at,
                        content_object=instance,
                        activity_type=const.TYPE_ACTIVITY_PRIZE
                    )
        activity.save()
        activity.receiving_users.add(instance.user)

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

        msg = (u"Congratulations, you have received a badge '%s'. " \
                + u"Check out <a href=\"%s\">your profile</a>.") \
                % (instance.badge.name, user.get_profile_url())

        user.message_set.create(message=msg)

def record_answer_accepted(instance, created, **kwargs):
    """
    when answer is accepted, we record this for question author 
    - who accepted it.
    """
    if not created and instance.accepted:
        activity = Activity(
                        user=instance.question.author,
                        active_at=datetime.datetime.now(),
                        content_object=instance,
                        activity_type=const.TYPE_ACTIVITY_MARK_ANSWER
                    )
        activity.save()
        receiving_users = instance.get_author_list(
                                    exclude_list = [instance.question.author]
                                )
        activity.receiving_users.add(*receiving_users)


def update_last_seen(instance, created, **kwargs):
    """
    when user has activities, we update 'last_seen' time stamp for him
    """
    #todo: in reality author of this activity must not be the receiving user
    #but for now just have this plug, so that last seen timestamp is not 
    #perturbed by the email update sender
    if instance.activity_type == const.TYPE_ACTIVITY_EMAIL_UPDATE_SENT:
        return
    user = instance.user
    user.last_seen = datetime.datetime.now()
    user.save()


def record_vote(instance, created, **kwargs):
    """
    when user have voted
    """
    if created:
        if instance.vote == 1:
            vote_type = const.TYPE_ACTIVITY_VOTE_UP
        else:
            vote_type = const.TYPE_ACTIVITY_VOTE_DOWN

        activity = Activity(
                        user=instance.user,
                        active_at=instance.voted_at,
                        content_object=instance,
                        activity_type=vote_type
                    )
        #todo: problem cannot access receiving user here
        activity.save()


def record_cancel_vote(instance, **kwargs):
    """
    when user canceled vote, the vote will be deleted.
    """
    activity = Activity(
                    user=instance.user, 
                    active_at=datetime.datetime.now(), 
                    content_object=instance, 
                    activity_type=const.TYPE_ACTIVITY_CANCEL_VOTE
                )
    #todo: same problem - cannot access receiving user here
    activity.save()


#todo: weird that there is no record delete answer or comment
#is this even necessary to keep track of?
def record_delete_question(instance, delete_by, **kwargs):
    """
    when user deleted the question
    """
    if instance.__class__ == "Question":
        activity_type = const.TYPE_ACTIVITY_DELETE_QUESTION
    else:
        activity_type = const.TYPE_ACTIVITY_DELETE_ANSWER

    activity = Activity(
                    user=delete_by, 
                    active_at=datetime.datetime.now(), 
                    content_object=instance, 
                    activity_type=activity_type
                )
    #no need to set receiving user here
    activity.save()

def record_mark_offensive(instance, mark_by, **kwargs):
    activity = Activity(
                    user=mark_by, 
                    active_at=datetime.datetime.now(), 
                    content_object=instance, 
                    activity_type=const.TYPE_ACTIVITY_MARK_OFFENSIVE
                )
    activity.save()
    receiving_users = instance.get_author_list(
                                        exclude_list = [mark_by]
                                    )
    activity.receiving_users.add(*receiving_users)

def record_update_tags(question, **kwargs):
    """
    when user updated tags of the question
    """
    activity = Activity(
                    user=question.author,
                    active_at=datetime.datetime.now(),
                    content_object=question,
                    activity_type=const.TYPE_ACTIVITY_UPDATE_TAGS
                )
    activity.save()

def record_favorite_question(instance, created, **kwargs):
    """
    when user add the question in him favorite questions list.
    """
    if created:
        activity = Activity(
                        user=instance.user, 
                        active_at=datetime.datetime.now(), 
                        content_object=instance, 
                        activity_type=const.TYPE_ACTIVITY_FAVORITE
                    )
        activity.save()
        receiving_users = instance.question.get_author_list(
                                            exclude_list = [instance.user]
                                        )
        activity.receiving_users.add(*receiving_users)

def record_user_full_updated(instance, **kwargs):
    activity = Activity(
                    user=instance, 
                    active_at=datetime.datetime.now(), 
                    content_object=instance, 
                    activity_type=const.TYPE_ACTIVITY_USER_FULL_UPDATED
                )
    activity.save()

def post_stored_anonymous_content(
                                sender,
                                user,
                                session_key,
                                signal,
                                *args,
                                **kwargs):

    aq_list = AnonymousQuestion.objects.filter(session_key = session_key)
    aa_list = AnonymousAnswer.objects.filter(session_key = session_key)
    #from askbot.conf import settings as askbot_settings
    if askbot_settings.EMAIL_VALIDATION == True:#add user to the record
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

#signal for User model save changes
django_signals.pre_save.connect(calculate_gravatar_hash, sender=User)
django_signals.post_save.connect(record_award_event, sender=Award)
django_signals.post_save.connect(notify_award_message, sender=Award)
django_signals.post_save.connect(record_answer_accepted, sender=Answer)
django_signals.post_save.connect(update_last_seen, sender=Activity)
django_signals.post_save.connect(record_vote, sender=Vote)
django_signals.post_save.connect(
                            record_favorite_question, 
                            sender=FavoriteQuestion
                        )
django_signals.post_delete.connect(record_cancel_vote, sender=Vote)

#change this to real m2m_changed with Django1.2
signals.delete_post_or_answer.connect(record_delete_question, sender=Question)
signals.delete_post_or_answer.connect(record_delete_question, sender=Answer)
signals.mark_offensive.connect(record_mark_offensive, sender=Question)
signals.mark_offensive.connect(record_mark_offensive, sender=Answer)
signals.tags_updated.connect(record_update_tags, sender=Question)
signals.user_updated.connect(record_user_full_updated, sender=User)
signals.user_logged_in.connect(post_stored_anonymous_content)
signals.post_updated.connect(
                           record_post_update_activity,
                           sender=Comment
                       )
signals.post_updated.connect(
                           record_post_update_activity,
                           sender=Answer
                       )
signals.post_updated.connect(
                           record_post_update_activity,
                           sender=Question
                       )
#post_syncdb.connect(create_fulltext_indexes)

#todo: wtf??? what is x=x about?
signals = signals

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
ValidationHash = ValidationHash
#AuthKeyUserAssociation = AuthKeyUserAssociation

__all__ = [
        'signals',

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
        'ValidationHash',
        #'AuthKeyUserAssociation',

        'User',
]
