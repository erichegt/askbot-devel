from base import *

from django.utils.translation import ugettext as _

class TagManager(models.Manager):
    UPDATE_USED_COUNTS_QUERY = (
        'UPDATE tag '
        'SET used_count = ('
            'SELECT COUNT(*) FROM question_tags '
            'INNER JOIN question ON question_id=question.id '
            'WHERE tag_id = tag.id AND question.deleted=False'
        ') '
        'WHERE id IN (%s)')

    def get_valid_tags(self, page_size):
      tags = self.all().filter(deleted=False).exclude(used_count=0).order_by("-id")[:page_size]
      return tags

    def get_or_create_multiple(self, names, user):
        """
        Fetches a list of Tags with the given names, creating any Tags
        which don't exist when necesssary.
        """
        tags = list(self.filter(name__in=names))
        #Set all these tag visible
        for tag in tags:
            if tag.deleted:
                tag.deleted = False
                tag.deleted_by = None
                tag.deleted_at = None
                tag.save()

        if len(tags) < len(names):
            existing_names = set(tag.name for tag in tags)
            new_names = [name for name in names if name not in existing_names]
            tags.extend([self.create(name=name, created_by=user)
                         for name in new_names if self.filter(name=name).count() == 0 and len(name.strip()) > 0])

        return tags

    def update_use_counts(self, tags):
        """Updates the given Tags with their current use counts."""
        if not tags:
            return
        cursor = connection.cursor()
        query = self.UPDATE_USED_COUNTS_QUERY % ','.join(['%s'] * len(tags))
        cursor.execute(query, [tag.id for tag in tags])
        transaction.commit_unless_managed()

    def get_tags_by_questions(self, questions):
        question_ids = []
        for question in questions:
            question_ids.append(question.id)

        question_ids_str = ','.join([str(id) for id in question_ids])
        related_tags = self.extra(
                tables=['tag', 'question_tags'],
                where=["tag.id = question_tags.tag_id AND question_tags.question_id IN (" + question_ids_str + ")"]
        ).distinct()

        return related_tags

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
    TAG_MARK_REASONS = (('good',_('interesting')),('bad',_('ignored')))
    tag = models.ForeignKey('Tag', related_name='user_selections')
    user = models.ForeignKey(User, related_name='tag_selections')
    reason = models.CharField(max_length=16, choices=TAG_MARK_REASONS)

    class Meta:
        app_label = 'forum'