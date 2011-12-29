import datetime
from django.db import models
from askbot.models.base import AnonymousContent
from askbot.models import content
from askbot import const


class Answer(content.Content):
    post_type = 'answer'
    question = models.ForeignKey('Question', related_name='answers')

    class Meta(content.Content.Meta):
        db_table = u'answer'


class AnonymousAnswer(AnonymousContent):
    question_post = models.ForeignKey('Post', related_name='anonymous_answers')

    def publish(self, user):
        added_at = datetime.datetime.now()
        Answer.objects.create_new(
            thread=self.question.thread,
            author=user,
            added_at=added_at,
            wiki=self.wiki,
            text=self.text
        )
        self.delete()
