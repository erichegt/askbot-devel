import datetime
import cgi
from django.db import models
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
#todo: maybe merge askbot.utils.markup and forum.utils.html
from askbot.utils import markup
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
                                        username__startswith = name_seed
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

    timestamp = post.get_time_of_last_edit()

    #create new mentions
    for u in newly_mentioned_users:
        from askbot.models.user import Activity
        Activity.objects.create_new_mention(
                                mentioned_whom = u,
                                mentioned_in = post,
                                mentioned_by = author,
                                mentioned_at = timestamp
                            )

    #todo: this is handled in signal because models for posts
    #are too spread out
    from askbot.models import signals
    signals.post_updated.send(
                    post = post, 
                    updated_by = author,
                    newly_mentioned_users = newly_mentioned_users,
                    timestamp = timestamp,
                    created = created,
                    sender = post.__class__
                )

    try:
        from askbot.conf import settings as askbot_settings
        if askbot_settings.GOOGLE_SITEMAP_CODE != '':
            ping_google()
    except Exception:
        logging.debug('cannot ping google - did you register with them?')

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
    revision   = models.PositiveIntegerField()
    author     = models.ForeignKey(User, related_name='%(class)ss')
    revised_at = models.DateTimeField()
    summary    = models.CharField(max_length=300, blank=True)
    text       = models.TextField()

    class Meta:
        abstract = True
        app_label = 'askbot'

    def as_html(self):
        """should return html representation of
        the revision
        """
        raise NotImplementedError()


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
