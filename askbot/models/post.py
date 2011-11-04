from django.db import models

from askbot.models.base import ContentRevision

#class Post(models.Model):
#    pass

class PostRevision(ContentRevision):
    answer = models.ForeignKey('askbot.Answer', related_name='revisions', null=True, blank=True)
    question = models.ForeignKey('askbot.Question', related_name='revisions', null=True, blank=True)

    class Meta:
        # INFO: This `unique_together` constraint might be problematic for databases in which
        #       2+ NULLs cannot be stored in an UNIQUE column.
        #       As far as I know MySQL, PostgreSQL and SQLite allow that so we're on the safe side.
        unique_together = (('answer', 'revision'), ('question', 'revision'))
        ordering = ('-revision',)
        app_label = 'askbot'
