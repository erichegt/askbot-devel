from django.db import models
from django.contrib.auth.models import User
from forum.models import Question
from django.core.urlresolvers import reverse
from django.utils.http import urlquote  as django_urlquote
from django.template.defaultfilters import slugify

class Book(models.Model):
    """
    Model for book info
    """
    user = models.ForeignKey(User)
    title = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    pages = models.SmallIntegerField()
    published_at = models.DateTimeField()
    publication = models.CharField(max_length=255)
    cover_img = models.CharField(max_length=255)
    tagnames = models.CharField(max_length=125)
    added_at = models.DateTimeField()
    last_edited_at = models.DateTimeField()
    questions = models.ManyToManyField(Question, related_name='book', db_table='book_question')

    def get_absolute_url(self):
        return reverse('book', args=[django_urlquote(slugify(self.short_name))])

    def __unicode__(self):
        return self.title
        
    class Meta:
        app_label = 'forum'
        db_table = u'book'

class BookAuthorInfo(models.Model):
    """
    Model for book author info
    """
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
    blog_url = models.CharField(max_length=255)
    added_at = models.DateTimeField()
    last_edited_at = models.DateTimeField()

    class Meta:
        app_label = 'forum'
        db_table = u'book_author_info'

class BookAuthorRss(models.Model):
    """
    Model for book author blog rss
    """
    user = models.ForeignKey(User)
    book = models.ForeignKey(Book)
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    rss_created_at = models.DateTimeField()
    added_at = models.DateTimeField()

    class Meta:
        app_label = 'forum'
        db_table = u'book_author_rss'