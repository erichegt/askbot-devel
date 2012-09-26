from django.test import TestCase
from django.contrib.auth.models import User, Group
from group_messaging.models import Message
from group_messaging.models import MessageMemo
from group_messaging.models import SenderList
from group_messaging.models import get_personal_group
from group_messaging.models import create_personal_group

MESSAGE_TEXT = 'test message text'

def create_user(name):
    """creates a user and a personal group,
    returns the created user"""
    user = User.objects.create_user(name, name + '@example.com')
    #note that askbot will take care of three lines below automatically
    try:
        group = get_personal_group(user)
    except Group.DoesNotExist:
        group = create_personal_group(user)
    group_name = '_personal_%d' % user.id
    group, created = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    return user

class ModelTests(TestCase):
    """test cases for the `private_messaging` models"""

    def setUp(self):
        self.sender = create_user('sender')
        self.recipient = create_user('recipient')

    def create_thread(self, recipients):
        return Message.objects.create_thread(
            sender=self.sender, recipients=recipients,
            text=MESSAGE_TEXT
        )

    def create_thread_for_user(self, user):
        group = get_personal_group(user)
        return self.create_thread([group])

    def test_create_thread_for_user(self):
        """the basic create thread with one recipient
        tests that the recipient is there"""
        message = self.create_thread_for_user(self.recipient)
        #message type is stored
        self.assertEqual(message.message_type, Message.STORED)
        #recipient is in the list of recipients
        recipients = set(message.recipients.all())
        recipient_group = get_personal_group(self.recipient)
        #sender_group = get_personal_group(self.sender) #maybe add this too
        expected_recipients = set([recipient_group])
        self.assertEqual(recipients, expected_recipients)
        #self.assertRaises(
        #    MessageMemo.DoesNotExist,
        #    MessageMemo.objects.get,
        #    message=message
        #)
        #make sure that the original senders memo to the root
        #message is marke ad seen
        memos = MessageMemo.objects.filter(
                                message=message,
                                user=self.sender
                            )
        self.assertEquals(memos.count(), 1)
        self.assertEqual(memos[0].status, MessageMemo.SEEN)

    def test_get_senders_for_user(self):
        """this time send thread to a real group test that
        member of the group has updated the sender list"""
        group = Group.objects.create(name='somegroup')
        self.recipient.groups.add(group)
        message = self.create_thread([group])
        senders = SenderList.objects.get_senders_for_user(self.recipient)
        self.assertEqual(set(senders), set([self.sender]))

    def test_create_thread_response(self):
        """create a thread with one response,
        then load thread for the user
        test that only the root message is retrieved"""
        root_message = self.create_thread_for_user(self.recipient)
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root_message
                                    )
        self.assertEqual(response.message_type, Message.STORED)

        #assert that there is only one "seen" memo for the response
        memos = MessageMemo.objects.filter(message=response)
        self.assertEqual(memos.count(), 1)
        self.assertEqual(memos[0].user, self.recipient)
        self.assertEqual(memos[0].status, MessageMemo.SEEN)

        #assert that recipients are the two people who are part of
        #this conversation
        recipients = set(response.recipients.all())
        sender_group = get_personal_group(self.sender)
        recipient_group = get_personal_group(self.recipient)
        expected_recipients = set([sender_group, recipient_group])
        self.assertEqual(recipients, expected_recipients)

    def test_get_threads_for_user(self):
        root_message = self.create_thread_for_user(self.recipient)
        threads = set(Message.objects.get_threads_for_user(self.sender))
        self.assertEqual(threads, set([]))
        threads = set(Message.objects.get_threads_for_user(self.recipient))
        self.assertEqual(threads, set([root_message]))

        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root_message
                                    )
        threads = set(Message.objects.get_threads_for_user(self.sender))
        self.assertEqual(threads, set([root_message]))
        threads = set(Message.objects.get_threads_for_user(self.recipient))
        self.assertEqual(threads, set([root_message]))
