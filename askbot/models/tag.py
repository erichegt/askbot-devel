from django.db import models
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.models.base import DeletableContent


class TagManager(models.Manager):
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
    def get_related_to_search(
                            self,
                            questions=None,
                            search_state=None,
                            ignored_tag_names=None
                        ):
        """must return at least tag names, along with use counts
        handle several cases to optimize the query performance
        """

        if search_state.is_default() or \
                questions.count() > search_state.page_size * 3:
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
