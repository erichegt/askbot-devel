import re
import logging
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from askbot.models.base import BaseQuerySetManager
from askbot import const
from askbot.conf import settings as askbot_settings
from askbot.utils import category_tree

def get_global_group():
    """Returns the global group,
    if necessary, creates one
    """
    #todo: when groups are disconnected from tags,
    #find comment as shown below in the test cases and
    #revert the values
    #todo: change groups to django groups
    group_name = askbot_settings.GLOBAL_GROUP_NAME
    try:
        return Tag.group_tags.get(name=group_name)
    except Tag.DoesNotExist:
        from askbot.models import get_admin
        return Tag.group_tags.get_or_create(
                            group_name=group_name,
                            user=get_admin(),
                            is_open=False
                        )

def delete_tags(tags):
    """deletes tags in the list"""
    tag_ids = [tag.id for tag in tags]
    Tag.objects.filter(id__in = tag_ids).delete()

def get_tags_by_names(tag_names):
    """returns query set of tags
    and a set of tag names that were not found
    """
    tags = Tag.objects.filter(name__in = tag_names)
    #if there are brand new tags, create them
    #and finalize the added tag list
    if tags.count() < len(tag_names):
        found_tag_names = set([tag.name for tag in tags])
        new_tag_names = set(tag_names) - found_tag_names
    else:
        new_tag_names = set()

    return tags, new_tag_names

def filter_tags_by_status(tags, status = None):
    """returns a list or a query set of tags which are accepted"""
    if isinstance(tags, models.query.QuerySet):
        return tags.filter(status = status)
    else:
        return [tag for tag in tags if tag.status == status]

def filter_accepted_tags(tags):
    return filter_tags_by_status(tags, status = Tag.STATUS_ACCEPTED)

def filter_suggested_tags(tags):
    return filter_tags_by_status(tags, status = Tag.STATUS_SUGGESTED)

def format_personal_group_name(user):
    #todo: after migration of groups away from tags,
    #this function will be moved somewhere else
    return '_internal_%s_%d' % (user.username, user.id)

def is_preapproved_tag_name(tag_name):
    """true if tag name is in the category tree
    or any other container of preapproved tags"""
    #get list of preapproved tags, to make exceptions for
    if askbot_settings.TAG_SOURCE == 'category-tree':
        return tag_name in category_tree.get_leaf_names()
    return False

def separate_unused_tags(tags):
    """returns two lists::
    * first where tags whose use counts are >0
    * second - with use counts == 0
    """
    used = list()
    unused = list()
    for tag in tags:
        if tag.used_count == 0:
            unused.append(tag)
        else:
            assert(tag.used_count > 0)
            used.append(tag)
    return used, unused

def tags_match_some_wildcard(tag_names, wildcard_tags):
    """Same as 
    :meth:`~askbot.models.tag.TagQuerySet.tags_match_some_wildcard`
    except it works on tag name strings
    """
    for tag_name in tag_names:
        for wildcard_tag in sorted(wildcard_tags):
            if tag_name.startswith(wildcard_tag[:-1]):
                return True
    return False

def get_mandatory_tags():
    """returns list of mandatory tags,
    or an empty list, if there aren't any"""
    from askbot.conf import settings as askbot_settings
    #TAG_SOURCE setting is hidden
    #and only is accessible via livesettings overrides
    if askbot_settings.TAG_SOURCE == 'category-tree':
        return []#hack: effectively we disable the mandatory tags feature
    else:
        #todo - in the future clean this up
        #we might need to have settings:
        #* prepopulated tags - json structure - either a flat list or a tree
        #  if structure is tree - then use some multilevel selector for choosing tags
        #  if it is a list - then make users click on tags to select them
        #* use prepopulated tags (boolean)
        #* tags are required
        #* regular users can create tags (boolean)
        #the category tree and the mandatory tag lists can be merged
        #into the same setting - and mandatory tags should use json
        #keep in mind that in the future multiword tags will be allowed
        raw_mandatory_tags = askbot_settings.MANDATORY_TAGS.strip()
        if len(raw_mandatory_tags) == 0:
            return []
        else:
            split_re = re.compile(const.TAG_SPLIT_REGEX)
            return split_re.split(raw_mandatory_tags)


class TagQuerySet(models.query.QuerySet):
    def get_valid_tags(self, page_size):
        tags = self.all().filter(deleted=False).exclude(used_count=0).order_by("-id")[:page_size]
        return tags

    def update_use_counts(self, tags):
        """Updates the given Tags with their current use counts."""
        for tag in tags:
            tag.used_count = tag.threads.count()
            tag.save()

    def mark_undeleted(self):
        """removes deleted(+at/by) marks"""
        self.update(#undelete them
            deleted = False,
            deleted_by = None,
            deleted_at = None
        )

    def tags_match_some_wildcard(self, wildcard_tags = None):
        """True if any one of the tags in the query set
        matches a wildcard

        :arg:`wildcard_tags` is an iterable of wildcard tag strings

        todo: refactor to use :func:`tags_match_some_wildcard`
        """
        for tag in self.all():
            for wildcard_tag in sorted(wildcard_tags):
                if tag.name.startswith(wildcard_tag[:-1]):
                    return True
        return False

    def get_by_wildcards(self, wildcards = None):
        """returns query set of tags that match the wildcard tags
        wildcard tag is guaranteed to end with an asterisk and has
        at least one character preceding the the asterisk. and there
        is only one asterisk in the entire name
        """
        if wildcards is None or len(wildcards) == 0:
            return self.none()
        first_tag = wildcards.pop()
        tag_filter = models.Q(name__startswith = first_tag[:-1])
        for next_tag in wildcards:
            tag_filter |= models.Q(name__startswith = next_tag[:-1])
        return self.filter(tag_filter)

    def get_related_to_search(self, threads, ignored_tag_names):
        """Returns at least tag names, along with use counts"""
        tags = self.filter(threads__in=threads).annotate(local_used_count=models.Count('id')).order_by('-local_used_count', 'name')
        if ignored_tag_names:
            tags = tags.exclude(name__in=ignored_tag_names)
        tags = tags.exclude(deleted = True)
        return list(tags[:50])


class TagManager(BaseQuerySetManager):
    """chainable custom filter query set manager
    for :class:``~askbot.models.Tag`` objects
    """
    def get_query_set(self):
        return TagQuerySet(self.model)

    def get_content_tags(self):
        """temporary function that filters out the group tags"""
        return self.annotate(
            member_count = models.Count('user_memberships')
        ).filter(
            member_count = 0
        )

    def create(self, name = None, created_by = None, **kwargs):
        """Creates a new tag"""
        if created_by.can_create_tags() or is_preapproved_tag_name(name):
            status = Tag.STATUS_ACCEPTED
        else:
            status = Tag.STATUS_SUGGESTED

        kwargs['created_by'] = created_by
        kwargs['name'] = name
        kwargs['status'] = status

        return super(TagManager, self).create(**kwargs)

    def create_suggested_tag(self, tag_names = None, user = None):
        """This function is not used, and will probably need
        to be retired. In the previous version we were sending
        email to admins when the new tags were created,
        now we have a separate page where new tags are listed.
        """
        #todo: stuff below will probably go after
        #tag moderation actions are implemented
        from askbot import mail
        from askbot.mail import messages
        body_text = messages.notify_admins_about_new_tags(
                                tags = tag_names,
                                user = user,
                                thread = self
                            )
        site_name = askbot_settings.APP_SHORT_NAME
        subject_line = _('New tags added to %s') % site_name
        mail.mail_moderators(
            subject_line,
            body_text,
            headers = {'Reply-To': user.email}
        )

        msg = _(
            'Tags %s are new and will be submitted for the '
            'moderators approval'
        ) % ', '.join(tag_names)
        user.message_set.create(message = msg)

    def create_in_bulk(self, tag_names = None, user = None):
        """creates tags by names. If user can create tags,
        then they are set status ``STATUS_ACCEPTED``,
        otherwise the status will be set to ``STATUS_SUGGESTED``.

        One exception: if suggested tag is in the category tree
        and source of tags is category tree - then status of newly
        created tag is ``STATUS_ACCEPTED``
        """

        #load suggested tags
        pre_suggested_tags = self.filter(
            name__in = tag_names, status = Tag.STATUS_SUGGESTED
        )

        #deal with suggested tags
        if user.can_create_tags():
            #turn previously suggested tags into accepted
            pre_suggested_tags.update(status = Tag.STATUS_ACCEPTED)
        else:
            #increment use count and add user to "suggested_by"
            for tag in pre_suggested_tags:
                tag.times_used += 1
                tag.suggested_by.add(user)
                tag.save()

        created_tags = list()
        pre_suggested_tag_names = list()
        for tag in pre_suggested_tags:
            pre_suggested_tag_names.append(tag.name)
            created_tags.append(tag)

        for tag_name in set(tag_names) - set(pre_suggested_tag_names):

            #status for the new tags is automatically set within the create()
            new_tag = Tag.objects.create(name = tag_name, created_by = user)
            created_tags.append(new_tag)

            if new_tag.status == Tag.STATUS_SUGGESTED:
                new_tag.suggested_by.add(user)

            #todo: here we have a chance to send a signal and notify
            #whoever wants about the new tag creation

        return created_tags

class GroupTagQuerySet(TagQuerySet):
    """Custom query set for the group"""

    def get_for_user(self, user=None, private=False):
        if private:
            global_group = get_global_group()
            return self.filter(
                        user_memberships__user=user
                    ).exclude(id=global_group.id)
        else:
            return self.filter(user_memberships__user = user)

    def get_all(self):
        return self.annotate(
            member_count = models.Count('user_memberships')
        ).filter(
            member_count__gt = 0
        )

    def get_by_name(self, group_name = None):
        return self.get(name = clean_group_name(group_name))


def clean_group_name(name):
    """group names allow spaces,
    tag names do not, so we use this method
    to replace spaces with dashes"""
    return re.sub('\s+', '-', name.strip())

class GroupTagManager(BaseQuerySetManager):
    """manager for group tags"""

    def get_query_set(self):
        return GroupTagQuerySet(self.model)

    def get_or_create(self, group_name = None, user = None, is_open=True):
        """creates a group tag or finds one, if exists"""
        #todo: here we might fill out the group profile

        #replace spaces with dashes
        group_name = clean_group_name(group_name)
        try:
            #iexact is important!!! b/c we don't want case variants
            #of tags
            tag = self.get(name__iexact = group_name)
        except self.model.DoesNotExist:
            tag = self.model(name = group_name, created_by = user)
            tag.save()
            from askbot.models.user import GroupProfile
            group_profile = GroupProfile(group_tag = tag, is_open=is_open)
            group_profile.save()
        return tag

class Tag(models.Model):
    #a couple of status constants
    STATUS_SUGGESTED = 0
    STATUS_ACCEPTED = 1

    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(User, related_name='created_tags')

    suggested_by = models.ManyToManyField(
        User, related_name='suggested_tags',
        help_text = 'Works only for suggested tags for tag moderation'
    )

    status = models.SmallIntegerField(default = STATUS_ACCEPTED)

    # Denormalised data
    used_count = models.PositiveIntegerField(default=0)

    deleted     = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    deleted_by  = models.ForeignKey(User, null=True, blank=True, related_name='deleted_tags')

    tag_wiki = models.OneToOneField(
                                'Post',
                                null=True,
                                related_name = 'described_tag'
                            )

    objects = TagManager()
    group_tags = GroupTagManager()

    class Meta:
        app_label = 'askbot'
        db_table = u'tag'
        ordering = ('-used_count', 'name')

    def __unicode__(self):
        return self.name

class MarkedTag(models.Model):
    TAG_MARK_REASONS = (
        ('good', _('interesting')),
        ('bad', _('ignored')),
        ('subscribed', _('subscribed')),
    )
    tag = models.ForeignKey('Tag', related_name='user_selections')
    user = models.ForeignKey(User, related_name='tag_selections')
    reason = models.CharField(max_length=16, choices=TAG_MARK_REASONS)

    class Meta:
        app_label = 'askbot'

def get_groups():
    return Tag.group_tags.get_all()

def get_group_names():
    #todo: cache me
    return get_groups().values_list('name', flat = True)
