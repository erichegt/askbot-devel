from django.test import TestCase
from django.contrib.auth.models import User, Group
from group_messaging.models import Message
from group_messaging.models import MessageMemo
from group_messaging.models import SenderList
from group_messaging.models import LastVisitTime
from group_messaging.models import get_personal_group
from group_messaging.models import create_personal_group
from group_messaging.views import ThreadsList
from mock import Mock
import time

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


    def get_view_context(self, view_class, data=None, user=None, method='GET'):
        spec = ['REQUEST', 'user']
        assert(method in ('GET', 'POST'))
        spec.append(method)
        request = Mock(spec=spec)
        request.REQUEST = data
        setattr(request, method, data)
        request.user = user
        return view_class().get_context(request)

    def setup_three_message_thread(self):
        """talk in this order: sender, recipient, sender"""
        root_message = self.create_thread_for_user(self.recipient)
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root_message
                                    )
        response2 = Message.objects.create_response(
                                        sender=self.sender,
                                        text='some response2',
                                        parent=response
                                    )
        return root_message, response, response2

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

    def test_get_threads(self):
        root_message = self.create_thread_for_user(self.recipient)
        threads = set(Message.objects.get_threads(recipient=self.sender))
        self.assertEqual(threads, set([]))
        threads = set(Message.objects.get_threads(recipient=self.recipient))
        self.assertEqual(threads, set([root_message]))

        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root_message
                                    )
        threads = set(Message.objects.get_threads(recipient=self.sender))
        self.assertEqual(threads, set([root_message]))
        threads = set(Message.objects.get_threads(recipient=self.recipient))
        self.assertEqual(threads, set([root_message]))

    def test_answer_to_deleted_thread_undeletes_thread(self):
        #setup: message, reply, responder deletes thread
        root_message = self.create_thread_for_user(self.recipient)
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root_message
                                    )
        memo1, created = MessageMemo.objects.get_or_create(
                                        message=root_message,
                                        user=self.recipient,
                                        status=MessageMemo.ARCHIVED
                                    )
        #OP sends reply to reply
        response2 = Message.objects.create_response(
                                        sender=self.sender,
                                        text='some response2',
                                        parent=response
                                    )

        context = self.get_view_context(
                                ThreadsList,
                                data={'sender_id': '-1'},
                                user=self.recipient
                            )

        self.assertEqual(len(context['threads']), 1)
        thread_id = context['threads'][0].id
        thread_data = context['threads_data'][thread_id]
        self.assertEqual(thread_data['status'], 'new')

    def test_deleting_thread_is_user_specific(self):
        """when one user deletes thread, that same thread
        should not end up deleted by another user
        """
        root, response, response2 = self.setup_three_message_thread()

        threads = Message.objects.get_threads(recipient=self.sender)
        self.assertEquals(threads.count(), 1)
        threads = Message.objects.get_threads(recipient=self.recipient)
        self.assertEquals(threads.count(), 1)

        memo1, created = MessageMemo.objects.get_or_create(
                                        message=root,
                                        user=self.recipient,
                                        status=MessageMemo.ARCHIVED
                                    )

        threads = Message.objects.get_threads(recipient=self.sender)
        self.assertEquals(threads.count(), 1)
        threads = Message.objects.get_threads(recipient=self.recipient)
        self.assertEquals(threads.count(), 0)
        threads = Message.objects.get_threads(
                                recipient=self.recipient, deleted=True
                            )
        self.assertEquals(threads.count(), 1)

    def test_user_specific_inboxes(self):
        self.create_thread_for_user(self.recipient)

        threads = Message.objects.get_threads(
                        recipient=self.recipient, sender=self.sender
                    )
        self.assertEqual(threads.count(), 1)
        threads = Message.objects.get_threads(
                        recipient=self.sender, sender=self.recipient
                    )
        self.assertEqual(threads.count(), 0)

    def test_new_response_marks_thread_heading_as_new(self):
        root = self.create_thread_for_user(self.recipient)
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root
                                    )
        #response must show as "new" to the self.sender
        context = self.get_view_context(
                                ThreadsList,
                                data={'sender_id': '-1'},
                                user=self.sender
                            )
        self.assertEqual(context['threads_data'][root.id]['status'], 'new')
        #"visit" the thread
        last_visit_time = LastVisitTime.objects.create(
                                                user=self.sender,
                                                message=root
                                            )
        time.sleep(1.5)

        #response must show as "seen"
        context = self.get_view_context(
                                ThreadsList,
                                data={'sender_id': '-1'},
                                user=self.sender
                            )
        self.assertEqual(context['threads_data'][root.id]['status'], 'seen')
        #self.recipient makes another response
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=response
                                    )
        #thread must be "new" again
        context = self.get_view_context(
                                ThreadsList,
                                data={'sender_id': '-1'},
                                user=self.sender
                            )
        self.assertEqual(context['threads_data'][root.id]['status'], 'new')

    def test_response_updates_thread_headline(self):
        root = self.create_thread_for_user(self.recipient)
        response = Message.objects.create_response(
                                        sender=self.recipient,
                                        text='some response',
                                        parent=root
                                    )
        self.assertEqual(root.headline, 'some response')
