from base import *

from question import Question

class AnswerManager(models.Manager):
    @staticmethod
    def create_new(cls, question=None, author=None, added_at=None, wiki=False, text='', email_notify=False):
        answer = Answer(
            question = question,
            author = author,
            added_at = added_at,
            wiki = wiki,
            html = text
        )
        if answer.wiki:
            answer.last_edited_by = answer.author
            answer.last_edited_at = added_at
            answer.wikified_at = added_at

        answer.save()

        #update question data
        question.last_activity_at = added_at
        question.last_activity_by = author
        question.save()
        Question.objects.update_answer_count(question)

        AnswerRevision.objects.create(
            answer     = answer,
            revision   = 1,
            author     = author,
            revised_at = added_at,
            summary    = CONST['default_version'],
            text       = text
        )

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

    def get_user_vote(self, user):
        if user.__class__.__name__ == "AnonymousUser":
            return None

        votes = self.votes.filter(user=user)
        if votes and votes.count() > 0:
            return votes[0]
        else:
            return None

    def get_latest_revision(self):
        return self.revisions.all()[0]

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
        #print user.id
        AnswerManager.create_new(question=self.question,wiki=self.wiki,
                            added_at=added_at,text=self.text,
                            author=user)
        self.delete()
