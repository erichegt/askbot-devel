"""badges data that is not stored in the database.
This data is static, so there is no point storing it in the db.

However, the database does have model BadgeData, that contains
additional mutable data pertaining to the badges - denormalized award counts
and lists of recipients
"""
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _
from askbot.models import BadgeData
from askbot import const

class Badge(object):
    """base class for the badges
    """
    def __init__(self,
                name = '', 
                level = None,
                description = None,
                multiple = False):

        self._name = name
        self.level = level
        self._description = description
        self.multiple = multiple

    def get_stored_data(self):
        data, created = BadgeData.objects.get_or_create(name = self.name)
        return data

    @property
    def awarded_count(self):
        return self.get_stored_data().awarded_count

    @property
    def awarded_to(self):
        return self.get_stored_data().awarded_to

    def award(self, recipient):
        """do award, the recipient was proven to deserve"""
        pass

    def consider_award(self, actor = None, context_object = None):
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
        super(Disciplined, self).__init__(
            key = 'disciplined',
            name = _('Disciplined'),
            description = _('Deleted own post with score of 3 or higher'),
            level = const.BRONZE_BADGE,
            multiple = True
        )

    def consider_award(self, actor = None, context_object = None):
        if context_object.author != actor:
            return
        if context_object.score > 2:
            self.award(actor)


BADGES = {
    'disciplined': Disciplined
}

def get_badge(name = None):
    """Get badge object by name, if none mathes the name
    raise KeyError
    """
    key = slugify(name)
    return BADGES[key]()
