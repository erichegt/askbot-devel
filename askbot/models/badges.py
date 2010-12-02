"""This file contains data on badges that is not stored in the database.
there are no django models in this file.
This data is static, so there is no point storing it in the db.

However, the database does have model BadgeData, that contains
additional mutable data pertaining to the badges - denormalized award counts
and lists of recipients.

BadgeData django model is located in askbot/models/meta.py

Badges in this file are connected with the contents of BadgeData
via key, determined as a slugified version of badge name.

To implement a new badge, one must create a subclass of Badge,
adde it to BADGES dictionary, register with event in EVENTS_TO_BADGES
and make sure that a signal `award_badges_signal` is sent with the
corresponding event name, actor (user object), context_object and optionally
- timestamp
"""
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext as _
from django.dispatch import Signal
from askbot.models.repute import BadgeData, Award
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils.decorators import auto_now_timestamp

class Badge(object):
    """base class for the badges
    """
    def __init__(self,
                key = '',
                name = '', 
                level = None,
                description = None,
                multiple = False):

        #key - must be an ASCII only word
        self.key = key 
        self.name = name
        self.level = level
        self.description = description
        self.multiple = multiple
        self.css_class = const.BADGE_CSS_CLASSES[self.level]

    def get_stored_data(self):
        data, created = BadgeData.objects.get_or_create(slug = self.key)
        return data

    @property
    def awarded_count(self):
        return self.get_stored_data().awarded_count

    @property
    def awarded_to(self):
        return self.get_stored_data().awarded_to

    @property
    def award_badge(self):
        """related name from `askbot.models.Award`
        the name of this property is confusing, but for now
        left in sync with the name on the `Award` model

        the goal is that any badge recalled from this
        module would behave just like the instance of BadgeData
        and vice versa
        """
        return self.get_stored_data().award_badge

    def get_level_display(self):
        """display name for the level of the badge"""
        return dict(const.BADGE_TYPE_CHOICES).get(self.level)

    def award(self, recipient = None, context_object = None, timestamp = None):
        """do award, the recipient was proven to deserve"""

        if self.multiple == False:
            if recipient.badges.filter(slug = self.key).count() != 0:
                return False
        else:
            content_type = ContentType.objects.get_for_model(context_object)
            filters = {
                'user': recipient,
                'object_id': context_object.id,
                'content_type': content_type,
                'badge__slug': self.key,
            }
            #multiple badge is not re-awarded for the same post
            if Award.objects.filter(**filters).count() != 0:
                return False

        badge = self.get_stored_data()
        award = Award(
                    user = recipient,
                    badge = badge,
                    awarded_at = timestamp,
                    content_object = context_object
                )
        award.save()#note: there are signals that listen to saving the Award
        return True

    def consider_award(self, actor = None, 
                context_object = None, timestamp = None):
        """This method should be implemented in subclasses
        actor - user who committed some action, context_object - 
        the object related to the award situation, e.g. an
        answer that is being upvoted

        the method should internally check who might be awarded and
        whether the situation is appropriate
        """
        raise NotImplementedError()

class Disciplined(Badge):
    def __init__(self):
        description = _(
            'Deleted own post with %(votes)s or more upvotes'
        ) % {'votes': askbot_settings.DISCIPLINED_BADGE_MIN_UPVOTES}
        super(Disciplined, self).__init__(
            key = 'disciplined',
            name = _('Disciplined'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
                    context_object = None, timestamp = None):

        if context_object.author != actor:
            return False
        if context_object.score >= \
            askbot_settings.DISCIPLINED_BADGE_MIN_UPVOTES:
            return self.award(actor, context_object, timestamp)

class PeerPressure(Badge):
    def __init__(self):
        description = _(
            'Deleted own post with %(votes)s or more downvotes'
        ) % {'votes': askbot_settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES}
        super(PeerPressure, self).__init__(
            key = 'peer-pressure',
            name = _('Peer Pressure'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
                    context_object = None, timestamp = None):

        if context_object.author != actor:
            return False
        if context_object.score <= \
            -1 * askbot_settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES:
            return self.award(actor, context_object, timestamp)
        return False

class Teacher(Badge):
    def __init__(self):
        description = _(
            'Received at least %(votes)s upvote for an answer for the first time'
        ) % {'votes': askbot_settings.TEACHER_BADGE_MIN_UPVOTES}
        super(Teacher, self).__init__(
            key = 'teacher',
            name = _('Teacher'),
            description = description,
            level = const.BRONZE_BADGE,
            multiple = False
        )

    def consider_award(self, actor = None, 
                context_object = None, timestamp = None):
        if context_object.post_type != 'answer':
            return False

        if context_object.score >= askbot_settings.TEACHER_BADGE_MIN_UPVOTES:
            return self.award(context_object.author, context_object, timestamp)
        return False

class QualityPost(Badge):
    """Generic Badge for Nice/Good/Great Question or Answer
    this badge is not used directly but is instantiated
    via subclasses

    The subclass has a responsibility to specify properties:
    * min_votes - a value from live settings
    * post_type - string 'question' or 'answer'
    * key, name, description, level and multiple - as intended in the Badge
    """
    def __init__(self):
        super(QualityPost, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = self.level,
            multiple = self.multiple
        )

    def consider_award(self, actor = None,
                context_object = None, timestamp = None):
        if context_object.post_type != 'answer':
            return False
        if context_object.score >= self.min_votes:
            return self.award(context_object.author, context_object, timestamp)
        return False

class NiceAnswer(QualityPost):
    def __new__(cls):
        self = super(QualityPost, cls).__new__(cls)
        self.name = _('Nice Answer')
        self.key = 'nice-answer'
        self.level = const.BRONZE_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.NICE_ANSWER_BADGE_MIN_UPVOTES
        self.description = _('Answer voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'answer'
        return self


ORIGINAL_DATA = """
    (_('Nice Question'), 3, _('nice-question'), _('Question voted up 10 times'), True, 0),
    (_('Pundit'), 3, _('pundit'), _('Left 10 comments with score of 10 or more'), False, 0),
    (_('Popular Question'), 3, _('popular-question'), _('Asked a question with 1,000 views'), True, 0),
    (_('Citizen patrol'), 3, _('citizen-patrol'), _('First flagged post'), False, 0),
    (_('Cleanup'), 3, _('cleanup'), _('First rollback'), False, 0),
    (_('Critic'), 3, _('critic'), _('First down vote'), False, 0),
    (_('Editor'), 3, _('editor'), _('First edit'), False, 0),
    (_('Organizer'), 3, _('organizer'), _('First retag'), False, 0),
    (_('Scholar'), 3, _('scholar'), _('First accepted answer on your own question'), False, 0),
    (_('Student'), 3, _('student'), _('Asked first question with at least one up vote'), False, 0),
    (_('Supporter'), 3, _('supporter'), _('First up vote'), False, 0),
    (_('Autobiographer'), 3, _('autobiographer'), _('Completed all user profile fields'), False, 0),
    (_('Self-Learner'), 3, _('self-learner'), _('Answered your own question with at least 3 up votes'), True, 0),
    (_('Great Answer'), 1, _('great-answer'), _('Answer voted up 100 times'), True, 0),
    (_('Great Question'), 1, _('great-question'), _('Question voted up 100 times'), True, 0),
    (_('Stellar Question'), 1, _('stellar-question'), _('Question favorited by 100 users'), True, 0),
    (_('Famous question'), 1, _('famous-question'), _('Asked a question with 10,000 views'), True, 0),
    (_('Alpha'), 2, _('alpha'), _('Actively participated in the private alpha'), False, 0),
    (_('Good Answer'), 2, _('good-answer'), _('Answer voted up 25 times'), True, 0),
    (_('Good Question'), 2, _('good-question'), _('Question voted up 25 times'), True, 0),
    (_('Favorite Question'), 2, _('favorite-question'), _('Question favorited by 25 users'), True, 0),
    (_('Civic duty'), 2, _('civic-duty'), _('Voted 300 times'), False, 0),
    (_('Strunk & White'), 2, _('strunk-and-white'), _('Edited 100 entries'), False, 0),
    (_('Generalist'), 2, _('generalist'), _('Active in many different tags'), False, 0),
    (_('Expert'), 2, _('expert'), _('Very active in one tag'), False, 0),
    (_('Yearling'), 2, _('yearling'), _('Active member for a year'), False, 0),
    (_('Notable Question'), 2, _('notable-question'), _('Asked a question with 2,500 views'), True, 0),
    (_('Enlightened'), 2, _('enlightened'), _('First answer was accepted with at least 10 up votes'), False, 0),
    (_('Beta'), 2, _('beta'), _('Actively participated in the private beta'), False, 0),
    (_('Guru'), 2, _('guru'), _('Accepted answer and voted up 40 times'), True, 0),
    (_('Necromancer'), 2, _('necromancer'), _('Answered a question more than 60 days later with at least 5 votes'), True, 0),
    (_('Taxonomist'), 2, _('taxonomist'), _('Created a tag used by 50 questions'), True, 0)
"""

BADGES = {
    'disciplined': Disciplined,
    'peer-pressure': PeerPressure,
    'teacher': Teacher,
    'nice-answer': NiceAnswer,
}

EVENTS_TO_BADGES = {
    'upvote_answer': (Teacher, NiceAnswer,),
    'delete_post': (Disciplined, PeerPressure,),
}

def get_badge(name = None):
    """Get badge object by name, if none mathes the name
    raise KeyError
    """
    key = slugify(name)
    return BADGES[key]()

def init_badges():
    """Calling this function will set up badge record
    int the database for each badge enumerated in the
    `BADGES` dictionary
    """
    #todo: maybe better to redo individual badges
    for key in BADGES.keys():
        get_badge(key).get_stored_data()

award_badges_signal = Signal(
                        providing_args=[
                            'actor', 'event', 'context_object', 'timestamp'
                        ]
                    )
#actor - user who triggers the event
#event - string name of the event, e.g 'downvote'
#context_object - database object related to the event, e.g. question

@auto_now_timestamp
def award_badges(event = None, actor = None, 
                context_object = None, timestamp = None, **kwargs):
    """function that is called when signal `award_badges_signal` is sent
    """

    try:
        consider_badges = EVENTS_TO_BADGES[event]
    except KeyError:
        raise NotImplementedError('event "%s" is not implemented' % event)

    for badge in consider_badges:
        badge().consider_award(actor, context_object, timestamp)

award_badges_signal.connect(award_badges)
