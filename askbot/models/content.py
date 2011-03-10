import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.db import models
from askbot.models.meta import Comment, Vote
from askbot.models.user import EmailFeedSetting
from askbot.models.tag import Tag, MarkedTag
from django.utils import html as html_utils

class Content(models.Model):
    """
        Base class for Question and Answer
    """
    author = models.ForeignKey(User, related_name='%(class)ss')
    added_at = models.DateTimeField(default=datetime.datetime.now)

    wiki = models.BooleanField(default=False)
    wikified_at = models.DateTimeField(null=True, blank=True)

    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, related_name='locked_%(class)ss')
    locked_at = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(default=0)
    vote_up_count = models.IntegerField(default=0)
    vote_down_count = models.IntegerField(default=0)

    comment_count = models.PositiveIntegerField(default=0)
    offensive_flag_count = models.SmallIntegerField(default=0)

    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(User, null=True, blank=True, related_name='last_edited_%(class)ss')

    html = models.TextField(null=True)#html rendition of the latest revision
    text = models.TextField(null=True)#denormalized copy of latest revision
    comments = generic.GenericRelation(Comment)
    votes = generic.GenericRelation(Vote)

    _use_markdown = True
    _escape_html = False #markdow does the escaping
    _urlize = False

    class Meta:
        abstract = True
        app_label = 'askbot'

    def get_comments(self):
        comments = self.comments.all().order_by('id')
        return comments

    #todo: maybe remove this wnen post models are unified
    def get_text(self):
        return self.text

    def get_snippet(self):
        """returns an abbreviated snippet of the content
        """
        return html_utils.strip_tags(self.html)[:120] + ' ...'

    def add_comment(self, comment=None, user=None, added_at=None):
        if added_at is None:
            added_at = datetime.datetime.now()
        if None in (comment ,user):
            raise Exception('arguments comment and user are required')

        #Comment = models.get_model('askbot','Comment')#todo: forum hardcoded
        comment = Comment(
                            content_object=self, 
                            comment=comment, 
                            user=user, 
                            added_at=added_at
                        )
        comment.parse_and_save(author = user)
        self.comment_count = self.comment_count + 1
        self.save()

        #tried to add this to bump updated question
        #in most active list, but it did not work
        #becase delayed email updates would be triggered
        #for cases where user did not subscribe for them
        #
        #need to redo the delayed alert sender
        #
        #origin_post = self.get_origin_post()
        #if origin_post == self:
        #    self.last_activity_at = added_at
        #    self.last_activity_by = user
        #else:
        #    origin_post.last_activity_at = added_at
        #    origin_post.last_activity_by = user
        #    origin_post.save()

        return comment

    def get_global_instant_notification_subscribers(self):
        """returns a set of subscribers to post according to tag filters
        both - subscribers who ignore tags or who follow only
        specific tags
        """
        tags = self.tags.all()

        subscriber_set = set()

        global_subscriptions = EmailFeedSetting.objects.filter(
                                                    feed_type = 'q_all',
                                                    frequency = 'i'
                                                )
        interesting_tag_selections = MarkedTag.objects.filter(
                                                    tag__in = tags,
                                                    reason = 'good'
                                                )
        global_interested_subscribers = User.objects.filter(
            tag_selections__in = interesting_tag_selections
        ).filter(
            notification_subscriptions__in = global_subscriptions
        ).filter(
            tag_filter_setting = 'interesting'
        )
        subscriber_set.update(global_interested_subscribers)

        ignored_tag_selections = MarkedTag.objects.filter(
                                                    tag__in = tags,
                                                    reason = 'bad'
                                                )

        global_non_ignoring_subscribers = User.objects.exclude(
            tag_selections__in = ignored_tag_selections
        ).filter(
            notification_subscriptions__in = global_subscriptions,
        ).filter(
            tag_filter_setting = 'ignored'
        )
        subscriber_set.update(global_non_ignoring_subscribers)
        return subscriber_set


    def get_instant_notification_subscribers(
                                self,
                                potential_subscribers = None,
                                mentioned_users = None,
                                exclude_list = None,
                            ):
        """get list of users who have subscribed to
        receive instant notifications for a given post
        this method works for questions and answers

        parameter "potential_subscribers" is not used here,
        but left for the uniformity of the interface (Comment method does use it)

        comment class has it's own variant which does have quite a bit
        of duplicated code at the moment
        """
        #print '------------------'
        #print 'in content function'
        subscriber_set = set()
        #print 'potential subscribers: ', potential_subscribers

        #1) mention subscribers - common to questions and answers
        if mentioned_users:
            mention_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                            potential_subscribers = mentioned_users,
                                            feed_type = 'm_and_c',
                                            frequency = 'i'
                                        )
            subscriber_set.update(mention_subscribers)

        origin_post = self.get_origin_post()

        #print origin_post

        #2) individually selected - make sure that users
        #are individual subscribers to this question
        selective_subscribers = origin_post.followed_by.all()
        #print 'question followers are ', [s for s in selective_subscribers]
        if selective_subscribers:
            selective_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                potential_subscribers = selective_subscribers,
                                feed_type = 'q_sel',
                                frequency = 'i'
                            )
            subscriber_set.update(selective_subscribers)
            #print 'selective subscribers: ', selective_subscribers

        #3) whole forum subscribers
        global_subscribers = origin_post.get_global_instant_notification_subscribers()
        subscriber_set.update(global_subscribers)

        #4) question asked by me (todo: not "edited_by_me" ???)
        question_author = origin_post.author
        if EmailFeedSetting.objects.filter(
                                            subscriber = question_author,
                                            frequency = 'i',
                                            feed_type = 'q_ask'
                                        ):
            subscriber_set.add(question_author)

        #4) questions answered by me -make sure is that people 
        #are authors of the answers to this question
        #todo: replace this with a query set method
        answer_authors = set()
        for answer in origin_post.answers.all():
            authors = answer.get_author_list()
            answer_authors.update(authors)

        if answer_authors:
            answer_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                    potential_subscribers = answer_authors,
                                    frequency = 'i',
                                    feed_type = 'q_ans',
                                )
            subscriber_set.update(answer_subscribers)
            #print 'answer subscribers: ', answer_subscribers

        #print 'exclude_list is ', exclude_list
        subscriber_set -= set(exclude_list)

        #print 'final subscriber set is ', subscriber_set
        return list(subscriber_set)

    def get_latest_revision(self):
        return self.revisions.all().order_by('-revised_at')[0]

    def get_latest_revision_number(self):
        return self.get_latest_revision().revision

    def get_time_of_last_edit(self):
        if self.last_edited_at:
            return self.last_edited_at
        else:
            return self.added_at

    def get_owner(self):
        return self.author

    def get_author_list(
                    self,
                    include_comments = False, 
                    recursive = False, 
                    exclude_list = None):

        #todo: there may be a better way to do these queries
        authors = set()
        authors.update([r.author for r in self.revisions.all()])
        if include_comments:
            authors.update([c.user for c in self.comments.all()])
        if recursive:
            if hasattr(self, 'answers'):
                for a in self.answers.exclude(deleted = True):
                    authors.update(a.get_author_list( include_comments = include_comments ) )
        if exclude_list:
            authors -= set(exclude_list)
        return list(authors)

    def passes_tag_filter_for_user(self, user):

        question = self.get_origin_post()
        if user.tag_filter_setting == 'interesting':
            #at least some of the tags must be marked interesting
            return user.has_affinity_to_question(
                                            question,
                                            affinity_type = 'like'
                                        )
        elif user.tag_filter_setting == 'ignored':
            return not user.has_affinity_to_question(
                                            question,
                                            affinity_type = 'dislike'
                                        )
        else:
            raise ValueError(
                        'unexpected User.tag_filter_setting %s' \
                        % user.tag_filter_setting
                    )

    def post_get_last_update_info(self):#todo: rename this subroutine
        when = self.added_at
        who = self.author
        if self.last_edited_at and self.last_edited_at > when:
            when = self.last_edited_at
            who = self.last_edited_by
        comments = self.comments.all()
        if len(comments) > 0:
            for c in comments:
                if c.added_at > when:
                    when = c.added_at
                    who = c.user
        return when, who
