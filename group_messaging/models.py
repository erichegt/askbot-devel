from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import User

MAX_TITLE_LENGTH = 80

#dummy parse message function
parse_message = lambda v: v

def get_personal_group_by_user_id(user_id):
    return Group.objects.get(name='_personal_%s' % user_id)


def get_personal_group(user):
    """returns personal group for the user"""
    return get_personal_group_by_user_id(user.id)


def create_personal_group(user):
    """creates a personal group for the user"""
    group = Group(name='_personal_%s' % user.id)
    group.save()
    return group


class SenderListManager(models.Manager):
    """model manager for the :class:`SenderList`"""

    def get_senders_for_user(self, user=None):
        """returns query set of :class:`User`"""
        user_groups = user.groups.all()
        lists = self.filter(recipient__in=user_groups)
        user_ids = lists.values_list(
                        'senders__id', flat=True
                    ).distinct()
        return User.objects.filter(id__in=user_ids)

class SenderList(models.Model):
    """a model to store denormalized data
    about who sends messages to any given person
    sender list is populated automatically
    as new messages are created
    """
    recipient = models.ForeignKey(Group, unique=True)
    senders = models.ManyToManyField(User)
    objects = SenderListManager()


class MessageMemo(models.Model):
    """A bridge between message recipients and messages
    these records are only created when user sees a message.
    The idea is that using groups as recipients, we can send
    messages to massive numbers of users, without cluttering
    the database.

    Instead we'll be creating a "seen" message after user
    reads the message.
    """
    SEEN = 0
    ARCHIVED = 1
    STATUS_CHOICES = (
        (SEEN, 'seen'),
        (ARCHIVED, 'archived')

    )
    user = models.ForeignKey(User)
    message = models.ForeignKey('Message')
    status = models.SmallIntegerField(
            choices=STATUS_CHOICES, default=SEEN
        )

    class Meta:
        unique_together = ('user', 'message')


class MessageManager(models.Manager):
    """model manager for the :class:`Message`"""

    def get_threads_for_user(self, user):
        user_groups = user.groups.all()
        return self.filter(
            root=None,
            message_type=Message.STORED,
            recipients__in=user_groups
        )

    def create(self, **kwargs):
        """creates a message"""
        root = kwargs.get('root', None)
        if root is None:
            parent = kwargs.get('parent', None)
            if parent:
                if parent.root:
                    root = parent.root
                else:
                    root = parent
        kwargs['root'] = root

        headline = kwargs.get('headline', kwargs['text'])
        kwargs['headline'] = headline[:MAX_TITLE_LENGTH]
        kwargs['html'] = parse_message(kwargs['text'])
        return super(MessageManager, self).create(**kwargs)

    def create_thread(self, sender=None, recipients=None, text=None):
        """creates a stored message and adds recipients"""
        message = self.create(
                    message_type=Message.STORED,
                    sender=sender,
                    text=text,
                )
        message.add_recipients(recipients)
        return message

    def create_response(self, sender=None, text=None, parent=None):
        message = self.create(
                    parent=parent,
                    message_type=Message.STORED,
                    sender=sender,
                    text=text,
                )
        #recipients are parent's recipients + sender
        #creator of response gets memo in the "read" status
        recipients = set(parent.recipients.all())
        senders_group = get_personal_group(parent.sender)
        recipients.add(senders_group)
        message.add_recipients(recipients, ignore_user=sender)
        #add author of the parent as a recipient to parent
        #but make sure to mute the message
        parent.add_recipients([senders_group], ignore_user=parent.sender)
        return message


class Message(models.Model):
    """the message model allowing users to send
    messages to other users and groups, via
    personal groups.
    """
    STORED = 0
    TEMPORARY = 1
    ONE_TIME = 2
    MESSAGE_TYPE_CHOICES = (
        (STORED, 'email-like message, stored in the inbox'),
        (ONE_TIME, 'will be shown just once'),
        (TEMPORARY, 'will be shown until certain time')
    )

    message_type = models.SmallIntegerField(
        choices=MESSAGE_TYPE_CHOICES,
        default=STORED,
    )
    
    sender = models.ForeignKey(User, related_name='sent_messages')
    recipients = models.ManyToManyField(Group)
    root = models.ForeignKey(
        'self', null=True,
        blank=True, related_name='descendants'
    )
    parent = models.ForeignKey(
        'self', null=True,
        blank=True, related_name='children'
    )
    headline = models.CharField(max_length=MAX_TITLE_LENGTH)
    text = models.TextField(
        null=True, blank=True,
        help_text='source text for the message, e.g. in markdown format'
    )
    html = models.TextField(
        null=True, blank=True,
        help_text='rendered html of the message'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now_add=True)
    active_until = models.DateTimeField(blank=True, null=True)

    objects = MessageManager()

    def add_recipients(self, recipients, ignore_user=None):
        """adds recipients to the message
        and updates the sender lists for all recipients
        todo: sender lists may be updated in a lazy way - per user

        `ignore_user` parameter is used to mark a specific user
        as not needing to receive a message as new, even if that
        user is a member of any of the recipient groups
        """
        if ignore_user:
            #crate a "seen" memo for the sender, because we
            #don't want to inform the user about his/her own post
            MessageMemo.objects.create(
                message=self, user=self.sender, status=MessageMemo.SEEN
            )

        self.recipients.add(*recipients)
        for recipient in recipients:
            sender_list, created = SenderList.objects.get_or_create(recipient=recipient)
            sender_list.senders.add(self.sender)
