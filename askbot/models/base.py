import datetime
import cgi
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.sitemaps import ping_google
#todo: maybe merge askbot.utils.markup and forum.utils.html
from askbot.utils import markup
from askbot.utils.diff import textDiff as htmldiff
from askbot.utils.html import sanitize_html
from django.utils import html
import logging

#todo: following methods belong to a future common post class
def parse_post_text(post):
    """typically post has a field to store raw source text
    in comment it is called .comment, in Question and Answer it is 
    called .text
    also there is another field called .html (consistent across models)
    so the goal of this function is to render raw text into .html
    and extract any metadata given stored in source (currently
    this metadata is limited by twitter style @mentions
    but there may be more in the future

    function returns a dictionary with the following keys
    html
    newly_mentioned_users - list of <User> objects
    removed_mentions - list of mention <Activity> objects - for removed ones
    """

    text = post.get_text()

    if post._escape_html:
        text = cgi.escape(text)

    if post._urlize:
        text = html.urlize(text)

    if post._use_markdown:
        text = sanitize_html(markup.get_parser().convert(text))

    #todo, add markdown parser call conditional on
    #post.use_markdown flag
    post_html = text
    mentioned_authors = list()
    removed_mentions = list()
    if '@' in text:
        op = post.get_origin_post()
        anticipated_authors = op.get_author_list(
                                    include_comments = True,
                                    recursive = True 
                                )

        extra_name_seeds = markup.extract_mentioned_name_seeds(text)

        extra_authors = set()
        for name_seed in extra_name_seeds:
            extra_authors.update(User.objects.filter(
                                        username__istartswith = name_seed
                                    )
                            )

        #it is important to preserve order here so that authors of post 
        #get mentioned first
        anticipated_authors += list(extra_authors)

        mentioned_authors, post_html = markup.mentionize_text(
                                                text,
                                                anticipated_authors
                                            )

        #find mentions that were removed and identify any previously
        #entered mentions so that we can send alerts on only new ones
        from askbot.models.user import Activity
        if post.pk is not None:
            #only look for previous mentions if post was already saved before
            prev_mention_qs = Activity.objects.get_mentions(
                                        mentioned_in = post
                                    )
            new_set = set(mentioned_authors)
            for prev_mention in prev_mention_qs:

                user = prev_mention.get_mentioned_user()
                if user is None:
                    continue
                if user in new_set:
                    #don't report mention twice
                    new_set.remove(user)
                else:
                    removed_mentions.append(prev_mention)
            mentioned_authors = list(new_set)

    data = {
        'html': post_html,
        'newly_mentioned_users': mentioned_authors,
        'removed_mentions': removed_mentions,
    }
    return data

#todo: when models are merged, it would be great to remove author parameter
def parse_and_save_post(post, author = None, **kwargs):
    """generic method to use with posts to be used prior to saving
    post edit or addition
    """

    assert(author is not None)

    last_revision = post.html
    data = post.parse()

    post.html = data['html']
    newly_mentioned_users = set(data['newly_mentioned_users']) - set([author]) 
    removed_mentions = data['removed_mentions']

    #a hack allowing to save denormalized .summary field for questions
    if hasattr(post, 'summary'):
        post.summary = strip_tags(post.html)[:120]

    #delete removed mentions
    for rm in removed_mentions:
        rm.delete()

    created = post.pk is None

    #this save must precede saving the mention activity
    #because generic relation needs primary key of the related object
    super(post.__class__, post).save(**kwargs)
    if last_revision:
        diff = htmldiff(last_revision, post.html)
    else:
        diff = post.get_snippet()

    timestamp = post.get_time_of_last_edit()

    #todo: this is handled in signal because models for posts
    #are too spread out
    from askbot.models import signals
    signals.post_updated.send(
                    post = post, 
                    updated_by = author,
                    newly_mentioned_users = newly_mentioned_users,
                    timestamp = timestamp,
                    created = created,
                    diff = diff,
                    sender = post.__class__
                )

    try:
        from askbot.conf import settings as askbot_settings
        if askbot_settings.GOOGLE_SITEMAP_CODE != '':
            ping_google()
    except Exception:
        logging.debug('cannot ping google - did you register with them?')

class BaseQuerySetManager(models.Manager):
    """a base class that allows chainable qustom filters
    on the query sets

    pattern from http://djangosnippets.org/snippets/562/

    Usage (the most basic example, all imports explicit for clarity):

    >>>import django.db.models.QuerySet
    >>>import django.db.models.Model
    >>>import askbot.models.base.BaseQuerySetManager
    >>>
    >>>class SomeQuerySet(django.db.models.QuerySet):
    >>>    def some_custom_filter(self, *args, **kwargs):
    >>>        return self #or any custom code
    >>>    #add more custom filters here
    >>>
    >>>class SomeManager(askbot.models.base.BaseQuerySetManager)
    >>>    def get_query_set(self):
    >>>        return SomeQuerySet(self.model)
    >>>
    >>>class SomeModel(django.db.models.Model)
    >>>    #add fields here
    >>>    objects = SomeManager()
    """
    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)

class UserContent(models.Model):
    user = models.ForeignKey(User, related_name='%(class)ss')

    class Meta:
        abstract = True
        app_label = 'askbot'


class MetaContent(models.Model):
    """
        Base class for Vote and Comment
    """
    content_type   = models.ForeignKey(ContentType)
    object_id      = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True
        app_label = 'askbot'

class DeletableContent(models.Model):
    deleted     = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    deleted_by  = models.ForeignKey(User, null=True, blank=True, related_name='deleted_%(class)ss')

    class Meta:
        abstract = True
        app_label = 'askbot'


class ContentRevision(models.Model):
    """
        Base class for QuestionRevision and AnswerRevision
    """
    QUESTION_REVISION_TEMPLATE_NO_TAGS = (
        '<h3>%(title)s</h3>\n'
        '<div class="text">%(html)s</div>\n'
    )

    QUESTION_REVISION = 1
    ANSWER_REVISION = 2
    REVISION_TYPE_CHOICES = (
        (QUESTION_REVISION, 'question'),
        (ANSWER_REVISION, 'answer'),
    )
    REVISION_TYPE_CHOICES_DICT = dict(REVISION_TYPE_CHOICES)

    revision_type = models.SmallIntegerField(choices=REVISION_TYPE_CHOICES)

    revision   = models.PositiveIntegerField()
    author     = models.ForeignKey(User, related_name='%(class)ss')
    revised_at = models.DateTimeField()
    summary    = models.CharField(max_length=300, blank=True)
    text       = models.TextField()

    # Question-specific fields
    title      = models.CharField(max_length=300, blank=True, default='')
    tagnames   = models.CharField(max_length=125, blank=True, default='')
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        abstract = True
        app_label = 'askbot'
        ordering = ('-revision',)

    def revision_type_str(self):
        return self.REVISION_TYPE_CHOICES_DICT[self.revision_type]

    def __unicode__(self):
        return u'%s - revision %s of %s' % (self.revision_type_str(), self.revision, self.title)

    def parent(self):
        if self.is_question_revision():
            return self.question
        elif self.is_answer_revision():
            return self.answer

    def save(self, **kwargs):
        """Determines the revistion type and then looks up the next available revision number if not set."""

        if not self.revision_type:
            # HACK: determine revision_type based on class name - until we have a better way or until make a switch to PostRevision
            #       After `revision_type` is set, we can just use it
            if self.__class__.__name__ == 'QuestionRevision':
                self.revision_type = self.QUESTION_REVISION
            elif self.__class__.__name__ == 'AnswerRevision':
                self.revision_type = self.ANSWER_REVISION

        if not self.revision:
            # TODO: Maybe use Max() aggregation?
            # TODO: Handle IntegrityError if revision id is already occupied?
            self.revision = self.parent().revisions.values_list('revision', flat=True)[0] + 1

        super(ContentRevision, self).save(**kwargs)

    def is_question_revision(self):
        return self.revision_type == self.QUESTION_REVISION

    def is_answer_revision(self):
        return self.revision_type == self.ANSWER_REVISION

    @models.permalink
    def get_absolute_url(self):
        if self.is_question_revision():
            return 'question_revisions', (self.question.id,), {}
        elif self.is_answer_revision():
            return 'answer_revisions', (), {'id':self.answer.id}

    def get_question_title(self):
        #INFO: ack-grepping shows that it's only used for Questions, so there's no code for Answers
        return self.question.title

    def as_html(self, **kwargs):
        markdowner = markup.get_parser()
        sanitized_html = sanitize_html(markdowner.convert(self.text))

        if self.is_question_revision():
            return self.QUESTION_REVISION_TEMPLATE_NO_TAGS % {
                'title': self.title,
                'html': sanitized_html
            }
        elif self.is_answer_revision():
            return sanitized_html



class AnonymousContent(models.Model):
    """
        Base class for AnonymousQuestion and AnonymousAnswer
    """
    session_key = models.CharField(max_length=40)  #session id for anonymous questions
    wiki = models.BooleanField(default=False)
    added_at = models.DateTimeField(default=datetime.datetime.now)
    ip_addr = models.IPAddressField(max_length=21) #allow high port numbers
    author = models.ForeignKey(User,null=True)
    text = models.TextField()
    summary = models.CharField(max_length=180)

    class Meta:
        abstract = True
        app_label = 'askbot'
