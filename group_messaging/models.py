"""models for the ``group_messaging`` app
"""
import datetime
from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import User

MAX_TITLE_LENGTH = 80
MAX_SENDERS_INFO_LENGTH = 64

#dummy parse message function
parse_message = lambda v: v

GROUP_NAME_TPL = '_personal_%s'

def get_personal_group_by_user_id(user_id):
    return Group.objects.get(name=GROUP_NAME_TPL % user_id)


def get_personal_groups_for_users(users):
    """for a given list of users return their personal groups"""
    group_names = [(GROUP_NAME_TPL % user.id) for user in users]
    return Group.objects.filter(name__in=group_names)


def get_personal_group(user):
    """returns personal group for the user"""
    return get_personal_group_by_user_id(user.id)


def create_personal_group(user):
    """creates a personal group for the user"""
    group = Group(name=GROUP_NAME_TPL % user.id)
    group.save()
    return group


class LastVisitTime(models.Model):
    """just remembers when a user has 
    last visited a given thread
    """
    user = models.ForeignKey(User)
    message = models.ForeignKey('Message')
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'message')


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

        message = super(MessageManager, self).create(**kwargs)
        #creator of message saw it by definition
        #crate a "seen" memo for the sender, because we
        #don't want to inform the user about his/her own post
        sender = kwargs['sender']
        MessageMemo.objects.create(
            message=message, user=sender, status=MessageMemo.SEEN
        )
        return message


    def create_thread(self, sender=None, recipients=None, text=None):
        """creates a stored message and adds recipients"""
        message = self.create(
                    message_type=Message.STORED,
                    sender=sender,
                    senders_info=sender.username,
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
        message.add_recipients(recipients)
        #add author of the parent as a recipient to parent
        parent.add_recipients([senders_group])
        #mark last active timestamp for the root message
        #so that we know that this thread was most recently
        #updated
        message.update_root_info()
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

    senders_info = models.CharField(
        max_length=MAX_SENDERS_INFO_LENGTH,
        default=''
    )#comma-separated list of a few names
    
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

    def add_recipients(self, recipients):
        """adds recipients to the message
        and updates the sender lists for all recipients
        todo: sender lists may be updated in a lazy way - per user
        """
        self.recipients.add(*recipients)
        for recipient in recipients:
            sender_list, created = SenderList.objects.get_or_create(recipient=recipient)
            sender_list.senders.add(self.sender)

    def update_root_info(self):
        """Update the last active at timestamp and
        the contributors info, if relevant.
        Root object will be saved to the database.
        """
        self.root.last_active_at = datetime.datetime.now()
        senders_names = self.root.senders_info.split(',')

        if self.sender.username in senders_names:
            senders_names.remove(self.sender.username)
        senders_names.insert(0, self.sender.username)

        self.root.senders_info = (','.join(senders_names))[:64]
        self.root.save()
