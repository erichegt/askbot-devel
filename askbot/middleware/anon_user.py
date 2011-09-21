"""middleware that allows anonymous users
receive messages using the now deprecated `message_set()`
interface of the user objects.

To allow anonymous users accept messages, a special
message manager is defined here, and :meth:`__deepcopy__()` method
added to the :class:`AnonymousUser` so that user could be pickled.

Secondly, it sends greeting message to anonymous users.
"""
from askbot.user_messages import create_message, get_and_delete_messages
from askbot.conf import settings as askbot_settings

class AnonymousMessageManager(object):
    """message manager for the anonymous user"""
    def __init__(self, request):
        self.request = request

    def create(self, message=''):
        """send message to anonymous user"""
        create_message(self.request, message)  

    def get_and_delete(self):
        messages = get_and_delete_messages(self.request)
        return messages

def dummy_deepcopy(*arg):
    """this is necessary to prevent deepcopy() on anonymous user object
    that now contains reference to request, which cannot be deepcopied
    """
    return None

class ConnectToSessionMessagesMiddleware(object):
    """middleware that attaches messages to anonymous users"""
    def process_request(self, request):
        if not request.user.is_authenticated():
            #plug on deepcopy which may be called by django db "driver"
            request.user.__deepcopy__ = dummy_deepcopy 
            #here request is linked to anon user
            request.user.message_set = AnonymousMessageManager(request) 
            request.user.get_and_delete_messages = \
                            request.user.message_set.get_and_delete

            #also set the first greeting one time per session only
            if 'greeting_set' not in request.session:
                request.session['greeting_set'] = True
                msg = askbot_settings.GREETING_FOR_ANONYMOUS_USER
                request.user.message_set.create(message=msg)
