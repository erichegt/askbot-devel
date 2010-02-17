from base import *

from question import Question, QuestionManager

class QuestionView(models.Model):
    question = models.ForeignKey(Question, related_name='viewed')
    who = models.ForeignKey(User, related_name='question_views')
    when = models.DateTimeField()

    class Meta:
        app_label = 'forum'

class FavoriteQuestion(models.Model):
    """A favorite Question of a User."""
    question      = models.ForeignKey(Question)
    user          = models.ForeignKey(User, related_name='user_favorite_questions')
    added_at = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label = 'forum'
        db_table = u'favorite_question'
    def __unicode__(self):
        return '[%s] favorited at %s' %(self.user, self.added_at)

class QuestionRevision(ContentRevision):
    """A revision of a Question."""
    question   = models.ForeignKey(Question, related_name='revisions')
    title      = models.CharField(max_length=300)
    tagnames   = models.CharField(max_length=125)

    class Meta(ContentRevision.Meta):
        db_table = u'question_revision'
        ordering = ('-revision',)

    def get_question_title(self):
        return self.question.title

    def get_absolute_url(self):
        #print 'in QuestionRevision.get_absolute_url()'
        return reverse('question_revisions', args=[self.question.id])

    def save(self, **kwargs):
        """Looks up the next available revision number."""
        if not self.revision:
            self.revision = QuestionRevision.objects.filter(
                question=self.question).values_list('revision',
                                                    flat=True)[0] + 1
        super(QuestionRevision, self).save(**kwargs)

    def __unicode__(self):
        return u'revision %s of %s' % (self.revision, self.title)

class AnonymousQuestion(AnonymousContent):
    title = models.CharField(max_length=300)
    tagnames = models.CharField(max_length=125)

    def publish(self,user):
        added_at = datetime.datetime.now()
        QuestionManager.create_new(title=self.title, author=user, added_at=added_at,
                                wiki=self.wiki, tagnames=self.tagnames,
                                summary=self.summary, text=self.text)
        self.delete()

from answer import Answer, AnswerManager

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