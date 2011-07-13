import re
from django.db import models
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.models.base import DeletableContent
from askbot.models.base import BaseQuerySetManager
from askbot import const

def tags_match_some_wildcard(tag_names, wildcard_tags):
    """Same as 
    :meth:`~askbot.models.tag.TagQuerySet.tags_match_some_wildcard`
    except it works on tag name strings
    """
    for tag_name in tag_names:
        for wildcard_tag in sorted(wildcard_tags):
            if tag_name.startswith(wildcard_tag[:-1]):
                return True
    return False

def get_mandatory_tags():
    """returns list of mandatory tags,
    or an empty list, if there aren't any"""
    from askbot.conf import settings as askbot_settings
    raw_mandatory_tags = askbot_settings.MANDATORY_TAGS.strip()
    if len(raw_mandatory_tags) == 0:
        return []
    else:
        split_re = re.compile(const.TAG_SPLIT_REGEX)
        return split_re.split(raw_mandatory_tags)

class TagQuerySet(models.query.QuerySet):
    UPDATE_USED_COUNTS_QUERY = """
        UPDATE tag 
        SET used_count = (
            SELECT COUNT(*) FROM question_tags 
            INNER JOIN question ON question_id=question.id
            WHERE tag_id = tag.id AND NOT question.deleted
        ) 
        WHERE id IN (%s);
    """

    def get_valid_tags(self, page_size):
        tags = self.all().filter(deleted=False).exclude(used_count=0).order_by("-id")[:page_size]
        return tags

    def update_use_counts(self, tags):
        """Updates the given Tags with their current use counts."""
        if not tags:
            return
        cursor = connection.cursor()
        query = self.UPDATE_USED_COUNTS_QUERY % ','.join(['%s'] * len(tags))
        cursor.execute(query, [tag.id for tag in tags])

        transaction.commit_unless_managed() 

    def tags_match_some_wildcard(self, wildcard_tags = None):
        """True if any one of the tags in the query set
        matches a wildcard

        :arg:`wildcard_tags` is an iterable of wildcard tag strings

        todo: refactor to use :func:`tags_match_some_wildcard`
        """
        for tag in self.all():
            for wildcard_tag in sorted(wildcard_tags):
                if tag.name.startswith(wildcard_tag[:-1]):
                    return True
        return False

    def get_by_wildcards(self, wildcards = None):
        """returns query set of tags that match the wildcard tags
        wildcard tag is guaranteed to end with an asterisk and has
        at least one character preceding the the asterisk. and there
        is only one asterisk in the entire name
        """
        if wildcards is None or len(wildcards) == 0:
            return self.none()
        first_tag = wildcards.pop()
        tag_filter = models.Q(name__startswith = first_tag[:-1])
        for next_tag in wildcards:
            tag_filter |= models.Q(name__startswith = next_tag[:-1])
        return self.filter(tag_filter)

    def get_related_to_search(
                            self,
                            questions = None,
                            search_state = None,
                            ignored_tag_names = None
                        ):
        """must return at least tag names, along with use counts
        handle several cases to optimize the query performance
        """

        if questions.count() > search_state.page_size * 3:
            """if we have too many questions or 
            search query is the most common - just return a list
            of top tags"""
            cheating = True
            tags = Tag.objects.all().order_by('-used_count')
        else:
            cheating = False
            #getting id's is necessary to avoid hitting a heavy query
            #on entire selection of questions. We actually want
            #the big questions query to hit only the page to be displayed
            q_id_list = questions.values_list('id', flat=True)
            tags = self.filter(
                    questions__id__in = q_id_list,
                ).annotate(
                    local_used_count=models.Count('id')
                ).order_by(
                    '-local_used_count'
                )

        if ignored_tag_names:
            tags = tags.exclude(name__in=ignored_tag_names)

        tags = tags.exclude(deleted = True)

        tags = tags[:50]#magic number
        if cheating:
            for tag in tags:
                tag.local_used_count = tag.used_count

        return tags


class TagManager(BaseQuerySetManager):
    """chainable custom filter query set manager
    for :class:``~askbot.models.Tag`` objects
    """
    def get_query_set(self):
        return TagQuerySet(self.model)

class Tag(DeletableContent):
    name            = models.CharField(max_length=255, unique=True)
    created_by      = models.ForeignKey(User, related_name='created_tags')
    # Denormalised data
    used_count = models.PositiveIntegerField(default=0)

    objects = TagManager()

    class Meta(DeletableContent.Meta):
        db_table = u'tag'
        ordering = ('-used_count', 'name')

    def __unicode__(self):
        return self.name

class MarkedTag(models.Model):
    TAG_MARK_REASONS = (('good', _('interesting')), ('bad', _('ignored')))
    tag = models.ForeignKey('Tag', related_name='user_selections')
    user = models.ForeignKey(User, related_name='tag_selections')
    reason = models.CharField(max_length=16, choices=TAG_MARK_REASONS)

    class Meta:
        app_label = 'askbot'
