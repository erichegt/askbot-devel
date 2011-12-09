import datetime
from django.db import models
from askbot.models.base import AnonymousContent
from askbot.models import content
from askbot import const

class AnswerManager(models.Manager):
    def create_new(self, thread, author, added_at, text, wiki=False, email_notify=False):
        # TODO: Some of this code will go to Post.objects.create_new
        answer = Answer(
            question = thread._question(),
            author = author,
            added_at = added_at,
            wiki = wiki,
            text = text,
            #.html field is denormalized by the save() call
        )
        if answer.wiki:
            answer.last_edited_by = answer.author
            answer.last_edited_at = added_at
            answer.wikified_at = added_at

        answer.parse_and_save(author=author)

        answer.add_revision(
            author = author,
            revised_at = added_at,
            text = text,
            comment = const.POST_STATUS['default_version'],
        )

        #update thread data
        thread.set_last_activity(last_activity_at=added_at, last_activity_by=author)
        thread.answer_count +=1
        thread.save()

        #set notification/delete
        if email_notify:
            thread.followed_by.add(author)
        else:
            thread.followed_by.remove(author)

        return answer

class Answer(content.Content):
    post_type = 'answer'
    question = models.ForeignKey('Question', related_name='answers')

    objects = AnswerManager()

    class Meta(content.Content.Meta):
        db_table = u'answer'


class AnonymousAnswer(AnonymousContent):
    question = models.ForeignKey('Question', related_name='anonymous_answers')

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
