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

class FirstVote(Badge):
    """this badge is not awarded directly, but through
    Supporter and Critic, which must provide
    * key, name and description properties through __new__ call
    """
    def __init__(self):
        super(FirstVote, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = const.BRONZE_BADGE,
            multiple = False
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type not in ('question', 'answer'):
            return False
        return self.award(actor, context_object, timestamp)

class Supporter(FirstVote):
    """first upvote"""
    def __new__(cls):
        self = super(Supporter, cls).__new__(cls)
        self.key = 'supporter'
        self.name = _('Supporter')
        self.description = _('First upvote')
        return self

class Critic(FirstVote):
    """like supporter, but for downvote"""
    def __new__(cls):
        self = super(Critic, cls).__new__(cls)
        self.key = 'critic'
        self.name = _('Critic')
        self.description = _('First downvote')
        return self

class SelfLearner(Badge):
    def __init__(self):
        description = _('Answered own question with at least %(num)s up votes')
        min_votes = askbot_settings.SELF_LEARNER_BADGE_MIN_UPVOTES
        super(SelfLearner, self).__init__(
            key = 'self-learner',
            name = _('Self-Learner'),
            description = description % {'num': min_votes},
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None,
            context_object = None, timestamp = None):
        if context_object.post_type != 'answer':
            return False

        min_upvotes = askbot_settings.SELF_LEARNER_BADGE_MIN_UPVOTES
        question = context_object.question
        answer = context_object

        if question.author == answer.author and answer.score >= min_upvotes:
            self.award(context_object.author, context_object, timestamp)

class QualityPost(Badge):
    """Generic Badge for Nice/Good/Great Question or Answer
    this badge is not used directly but is instantiated
    via subclasses created via __new__() method definitions

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
        if context_object.post_type not in ('answer', 'question'):
            return False
        if context_object.score >= self.min_votes:
            return self.award(context_object.author, context_object, timestamp)
        return False

class NiceAnswer(QualityPost):
    def __new__(cls):
        self = super(NiceAnswer, cls).__new__(cls)
        self.name = _('Nice Answer')
        self.key = 'nice-answer'
        self.level = const.BRONZE_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.NICE_ANSWER_BADGE_MIN_UPVOTES
        self.description = _('Answer voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'answer'
        return self

class GoodAnswer(QualityPost):
    def __new__(cls):
        self = super(GoodAnswer, cls).__new__(cls)
        self.name = _('Good Answer')
        self.key = 'good-answer'
        self.level = const.SILVER_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GOOD_ANSWER_BADGE_MIN_UPVOTES
        self.description = _('Answer voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'answer'
        return self

class GreatAnswer(QualityPost):
    def __new__(cls):
        self = super(GreatAnswer, cls).__new__(cls)
        self.name = _('Great Answer')
        self.key = 'great-answer'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GREAT_ANSWER_BADGE_MIN_UPVOTES
        self.description = _('Answer voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'answer'
        return self

class NiceQuestion(QualityPost):
    def __new__(cls):
        self = super(NiceQuestion, cls).__new__(cls)
        self.name = _('Nice Question')
        self.key = 'nice-question'
        self.level = const.BRONZE_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.NICE_QUESTION_BADGE_MIN_UPVOTES
        self.description = _('Question voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'question'
        return self

class GoodQuestion(QualityPost):
    def __new__(cls):
        self = super(GoodQuestion, cls).__new__(cls)
        self.name = _('Good Question')
        self.key = 'good-question'
        self.level = const.SILVER_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GOOD_QUESTION_BADGE_MIN_UPVOTES
        self.description = _('Question voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'question'
        return self

class GreatQuestion(QualityPost):
    def __new__(cls):
        self = super(GreatQuestion, cls).__new__(cls)
        self.name = _('Great Question')
        self.key = 'great-question'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_votes = askbot_settings.GREAT_QUESTION_BADGE_MIN_UPVOTES
        self.description = _('Question voted up %(num)s times') % {'num': self.min_votes}
        self.post_type = 'question'
        return self

class Student(QualityPost):
    def __new__(cls):
        self = super(Student , cls).__new__(cls)
        self.name = _('Student')
        self.key = 'student'
        self.level = const.BRONZE_BADGE
        self.multiple = False
        self.min_votes = 1
        self.description = _('Asked first question with at least one up vote')
        self.post_type = 'question'
        return self

class FrequentedQuestion(Badge):
    """this badge is not awarded directly
    but must be subclassed by Popular, Notable and Famous Question
    badges via __new__() method definitions

    The subclass has a responsibility to specify properties:
    * min_views - a value from live settings
    * key, name, description and level and multiple - as intended in the Badge
    """
    def __init__(self):
        super(FrequentedQuestion, self).__init__(
            key = self.key,
            name = self.name,
            description = self.description,
            level = self.level,
            multiple = True
        )

    def consider_award(self, actor = None,
                context_object = None, timestamp = None):
        if context_object.post_type != 'question':
            return False
        if context_object.view_count >= self.min_views:
            return self.award(context_object.author, context_object, timestamp)
        return False

class PopularQuestion(FrequentedQuestion):
    def __new__(cls):
        self = super(PopularQuestion, cls).__new__(cls)
        self.name = _('Popular Question')
        self.key = 'popular-question'
        self.level = const.BRONZE_BADGE
        self.min_views = askbot_settings.POPULAR_QUESTION_BADGE_MIN_VIEWS
        self.description = _('Asked a question with %(views)s views') \
                            % {'views' : self.min_views}
        return self

class NotableQuestion(FrequentedQuestion):
    def __new__(cls):
        self = super(NotableQuestion, cls).__new__(cls)
        self.name = _('Notable Question')
        self.key = 'notable-question'
        self.level = const.SILVER_BADGE
        self.min_views = askbot_settings.NOTABLE_QUESTION_BADGE_MIN_VIEWS
        self.description = _('Asked a question with %(views)s views') \
                            % {'views' : self.min_views}
        return self

class FamousQuestion(FrequentedQuestion):
    def __new__(cls):
        self = super(FamousQuestion, cls).__new__(cls)
        self.name = _('Famous Question')
        self.key = 'famous-question'
        self.level = const.GOLD_BADGE
        self.multiple = True
        self.min_views = askbot_settings.FAMOUS_QUESTION_BADGE_MIN_VIEWS
        self.description = _('Asked a question with %(views)s views') \
                            % {'views' : self.min_views}
        return self

ORIGINAL_DATA = """
    (_('Civic duty'), 2, _('civic-duty'), _('Voted 300 times'), False, 0),

    (_('Enlightened'), 2, _('enlightened'), _('First answer was accepted with at least 10 up votes'), False, 0),
    (_('Guru'), 2, _('guru'), _('Accepted answer and voted up 40 times'), True, 0),

    (_('Necromancer'), 2, _('necromancer'), _('Answered a question more than 60 days later with at least 5 votes'), True, 0),

    (_('Scholar'), 3, _('scholar'), _('First accepted answer on your own question'), False, 0),
    (_('Pundit'), 3, _('pundit'), _('Left 10 comments with score of 10 or more'), False, 0),
    (_('Citizen patrol'), 3, _('citizen-patrol'), _('First flagged post'), False, 0),

    (_('Cleanup'), 3, _('cleanup'), _('First rollback'), False, 0),

    (_('Editor'), 3, _('editor'), _('First edit'), False, 0),
    (_('Strunk & White'), 2, _('strunk-and-white'), _('Edited 100 entries'), False, 0),
    (_('Organizer'), 3, _('organizer'), _('First retag'), False, 0),

    (_('Autobiographer'), 3, _('autobiographer'), _('Completed all user profile fields'), False, 0),

    (_('Stellar Question'), 1, _('stellar-question'), _('Question favorited by 100 users'), True, 0),
    (_('Favorite Question'), 2, _('favorite-question'), _('Question favorited by 25 users'), True, 0),

    (_('Alpha'), 2, _('alpha'), _('Actively participated in the private alpha'), False, 0),

    (_('Generalist'), 2, _('generalist'), _('Active in many different tags'), False, 0),
    (_('Expert'), 2, _('expert'), _('Very active in one tag'), False, 0),
    (_('Taxonomist'), 2, _('taxonomist'), _('Created a tag used by 50 questions'), True, 0)

    (_('Yearling'), 2, _('yearling'), _('Active member for a year'), False, 0),
    (_('Beta'), 2, _('beta'), _('Actively participated in the private beta'), False, 0),
"""

BADGES = {
    'disciplined': Disciplined,
    'peer-pressure': PeerPressure,
    'teacher': Teacher,
    'student': Student,
    'supporter': Supporter,
    'self-learner': SelfLearner,
    'nice-answer': NiceAnswer,
    'good-answer': GoodAnswer,
    'great-answer': GreatAnswer,
    'nice-question': NiceQuestion,
    'good-question': GoodQuestion,
    'great-question': GreatQuestion,
    'popular-question': PopularQuestion,
    'notable-question': NotableQuestion,
    'famous-question': FamousQuestion,
    'critic': Critic,
}

#events are sent as a parameter via signal award_badges_signal
#from appropriate locations in the code of askbot application
#most likely - from manipulator functions that are added to the User objects
EVENTS_TO_BADGES = {
    'upvote_answer': (
                    Teacher, NiceAnswer, GoodAnswer,
                    GreatAnswer, Supporter, SelfLearner
                ),
    'upvote_question': (
                    NiceQuestion, GoodQuestion,
                    GreatQuestion, Student, Supporter
                ),
    'downvote': (Critic,),#no regard for question or answer for now
    'delete_post': (Disciplined, PeerPressure,),
    'view_question': (PopularQuestion, NotableQuestion, FamousQuestion,),
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
    #so that get_stored_data() is called implicitly
    #from the __init__ function?
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
        badge_instance = badge()
        badge_instance.consider_award(actor, context_object, timestamp)

award_badges_signal.connect(award_badges)
