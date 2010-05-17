from base import *
#todo: take care of copy-paste markdowner stuff maybe make html automatic field?
from forum.const import CONST
from markdown2 import Markdown
from django.utils.html import strip_tags 
from forum.utils.html import sanitize_html
import datetime
markdowner = Markdown(html4tags=True)

from question import Question

class AnswerManager(models.Manager):
    def create_new(self, question=None, author=None, added_at=None, wiki=False, text='', email_notify=False):
        answer = Answer(
            question = question,
            author = author,
            added_at = added_at,
            wiki = wiki,
            text = text,
            html = sanitize_html(markdowner.convert(text)),
        )
        if answer.wiki:
            answer.last_edited_by = answer.author
            answer.last_edited_at = added_at
            answer.wikified_at = added_at

        answer.save()

        answer.add_revision(
            revised_by=author,
            revised_at=added_at,
            text=text,
            comment=CONST['default_version'],
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

    #GET_ANSWERS_FROM_USER_QUESTIONS = u'SELECT answer.* FROM answer INNER JOIN question ON answer.question_id = question.id WHERE question.author_id =%s AND answer.author_id <> %s'
    def get_answers_from_question(self, question, user=None):
        """
        Retrieves visibile answers for the given question. Delete answers
        are only visibile to the person who deleted them.
        """

        if user is None or not user.is_authenticated():
            return self.filter(question=question, deleted=False)
        else:
            return self.filter(models.Q(question=question),
                               models.Q(deleted=False) | models.Q(deleted_by=user))

    #todo: I think this method is not being used anymore, I'll just comment it for now
    #def get_answers_from_questions(self, user_id):
    #    """
    #    Retrieves visibile answers for the given question. Which are not included own answers
    #    """
    #    cursor = connection.cursor()
    #    cursor.execute(self.GET_ANSWERS_FROM_USER_QUESTIONS, [user_id, user_id])
    #    return cursor.fetchall()

class Answer(Content, DeletableContent):
    question = models.ForeignKey('Question', related_name='answers')
    accepted    = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    objects = AnswerManager()

    class Meta(Content.Meta):
        db_table = u'answer'

    def apply_edit(self, edited_at=None, edited_by=None, text=None, comment=None, wiki=False):

        if text is None:
            text = self.get_latest_revision().text
        if edited_at is None:
            edited_at = datetime.datetime.now()
        if edited_by is None:
            raise Exception('edited_by is required')

        self.last_edited_at = edited_at
        self.last_edited_by = edited_by
        self.html = sanitize_html(markdowner.convert(text))
        self.text = text
        #todo: bug wiki has no effect here
        self.save()

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
                comment = CONST['default_version']
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
