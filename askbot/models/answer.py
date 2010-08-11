import datetime
from django.db import models
from django.utils.http import urlquote  as django_urlquote
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from askbot.models.base import AnonymousContent, DeletableContent
from askbot.models.base import ContentRevision
from askbot.models.base import parse_post_text, parse_and_save_post
from askbot.models import content
from askbot.models.question import Question
from askbot import const


class AnswerManager(models.Manager):
    def create_new(
                self, 
                question=None, 
                author=None, 
                added_at=None, 
                wiki=False, 
                text='', 
                email_notify=False
            ):

        answer = Answer(
            question = question,
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

        answer.parse_and_save(author = author)

        answer.add_revision(
            revised_by = author,
            revised_at = added_at,
            text = text,
            comment = const.POST_STATUS['default_version'],
        )

        #update question data
        question.last_activity_at = added_at
        question.last_activity_by = author
        question.save()
        Question.objects.update_answer_count(question)

        #set notification/delete
        if email_notify:
            if author not in question.followed_by.all():
                question.followed_by.add(author)
        else:
            #not sure if this is necessary. ajax should take care of this...
            try:
                question.followed_by.remove(author)
            except:
                pass
        return answer

    def get_author_list(self, **kwargs):
        authors = set()
        for answer in self:
            authors.update(answer.get_author_list(**kwargs))
        return list(authors)

    #todo: I think this method is not being used anymore, I'll just comment it for now
    #def get_answers_from_questions(self, user_id):
    #    """
    #    Retrieves visibile answers for the given question. Which are not included own answers
    #    """
    #    cursor = connection.cursor()
    #    cursor.execute(self.GET_ANSWERS_FROM_USER_QUESTIONS, [user_id, user_id])
    #    return cursor.fetchall()

class Answer(content.Content, DeletableContent):
    question = models.ForeignKey('Question', related_name='answers')
    accepted    = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    objects = AnswerManager()

    class Meta(content.Content.Meta):
        db_table = u'answer'

    parse = parse_post_text
    parse_and_save = parse_and_save_post

    def get_updated_activity_data(self, created = False):
        #todo: simplify this to always return latest revision for the second
        #part
        if created:
            return const.TYPE_ACTIVITY_ANSWER, self
        else:
            latest_revision = self.get_latest_revision()
            return const.TYPE_ACTIVITY_UPDATE_ANSWER, latest_revision

    def apply_edit(self, edited_at=None, edited_by=None, text=None, comment=None, wiki=False):

        if text is None:
            text = self.get_latest_revision().text
        if edited_at is None:
            edited_at = datetime.datetime.now()
        if edited_by is None:
            raise Exception('edited_by is required')

        self.last_edited_at = edited_at
        self.last_edited_by = edited_by
        #self.html is denormalized in save()
        self.text = text
        #todo: bug wiki has no effect here
        self.parse_and_save(author = edited_by)

        self.add_revision(
            revised_by=edited_by,
            revised_at=edited_at,
            text=text,
            comment=comment
        )

        self.question.last_activity_at = edited_at
        self.question.last_activity_by = edited_by
        self.question.save()

    def add_revision(self, revised_by=None, revised_at=None, text=None, comment=None):
        if None in (revised_by, revised_at, text):
            raise Exception('arguments revised_by, revised_at and text are required')
        rev_no = self.revisions.all().count() + 1
        if comment in (None, ''):
            if rev_no == 1:
                comment = const.POST_STATUS['default_version']
            else:
                comment = 'No.%s Revision' % rev_no
        return AnswerRevision.objects.create(
                                  answer=self,
                                  author=revised_by,
                                  revised_at=revised_at,
                                  text=text,
                                  summary=comment,
                                  revision=rev_no
                                  )

    def get_origin_post(self):
        return self.question

    def get_response_receivers(self, exclude_list = None):
        """get list of users interested in this response
        update based on their participation in the question
        activity

        exclude_list is required and normally should contain
        author of the updated so that he/she is not notified of
        the response
        """
        assert(exclude_list is not None)
        receiving_users = set()
        receiving_users.update(
                            self.get_author_list(
                                include_comments = True 
                            )
                        )
        receiving_users.update(
                            self.question.get_author_list(
                                    include_comments = True
                                )
                        )
        for answer in self.question.answers.all():
            receiving_users.update(answer.get_author_list())

        receiving_users -= set(exclude_list)

        return list(receiving_users)

    def get_user_vote(self, user):
        if user.__class__.__name__ == "AnonymousUser":
            return None

        votes = self.votes.filter(user=user)
        if votes and votes.count() > 0:
            return votes[0]
        else:
            return None

    def get_question_title(self):
        return self.question.title

    def get_absolute_url(self):
        return '%s%s#%s' % (reverse('question', args=[self.question.id]), django_urlquote(slugify(self.question.title)), self.id)

    def __unicode__(self):
        return self.html
        

class AnswerRevision(ContentRevision):
    """A revision of an Answer."""
    answer     = models.ForeignKey('Answer', related_name='revisions')

    def get_absolute_url(self):
        return reverse('answer_revisions', kwargs={'id':self.answer.id})

    def get_question_title(self):
        return self.answer.question.title

    class Meta(ContentRevision.Meta):
        db_table = u'answer_revision'
        ordering = ('-revision',)

    def save(self, **kwargs):
        """Looks up the next available revision number if not set."""
        if not self.revision:
            self.revision = AnswerRevision.objects.filter(
                answer=self.answer).values_list('revision',
                                                flat=True)[0] + 1
        super(AnswerRevision, self).save(**kwargs)

class AnonymousAnswer(AnonymousContent):
    question = models.ForeignKey('Question', related_name='anonymous_answers')

    def publish(self,user):
        added_at = datetime.datetime.now()
        Answer.objects.create_new(question=self.question,wiki=self.wiki,
                            added_at=added_at,text=self.text,
                            author=user)
        self.delete()
