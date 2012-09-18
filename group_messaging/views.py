"""semi-views for the `group_messaging` application
These are not really views - rather context generator
functions, to be used separately, when needed.

For example, some other application can call these
in order to render messages within the page.

Notice that :mod:`urls` module decorates all these functions
and turns them into complete views
"""
import functools
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.forms import IntegerField
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.utils import simplejson
from group_messages.models import Message
from group_messages.models import MessageMemo
from group_messages.models import SenderList
from group_messages.models import get_personal_group_by_id

class InboxView(object):
    """custom class-based view
    to be used for pjax use and for generation
    of content in the traditional way"""
    template_name = None #this needs to be set

    def get(self, request, *args, **kwargs):
        context = self.get_context(request, *args, **kwargs)
        #todo: load template with Coffin and render it
        return HttpResponse(json, mimetype='application/json')

    def get_context(self, request, *args, **kwargs):
        """Should return the context dictionary"""
        return {}

    def as_pjax(self):
        """returns the view function - for the urls.py"""
        def view_function(request, *args, **kwargs):
            """the actual view function"""
            if request.user.is_anonymous():
                raise PermissionDenied()
            if request.is_ajax() is False:
                raise PermissionDenied()

            if request.method == 'GET':
                return self.get(request, *args, **kwargs)
            elif request.method == 'POST':
                return self.post(request, *args, **kwargs)
            else:
                raise NotImplementedError
        return view_function


def require_login(view_func):
    @functools.wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied()
    return wrapped


def ajax(view_func):
    @functools.wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.is_ajax():
            result = view_func(request, *args, **kwargs)
            json = simplejson.dumps(result)
            return HttpResponse(json, mimetype='application/json')
        else:
            raise PermissionDenied()


class NewThread(InboxView):
    template_name = 'new_thread.html'

    def post(self, request):
        recipient_id = IntegerField().clean(request.POST['recipient_id'])
        recipient = get_personal_group_by_id(recipient_id)
        message = Message.objects.create_thread(
                        sender=request.user,
                        recipients=[recipient],
                        text=request.POST['text']
                    )
        return {'message_id': message.id}


class NewResponse(InboxView):
    def get(self, request):
        raise PermissionDenied()

    def post(self, request):
        parent_id = IntegerField().clean(request.POST['parent_id'])
        parent = Message.objects.get(id=parent_id)
        message = Message.objects.create_response(
                                        sender=request.user,
                                        text=request.POST['text'],
                                        parent=parent
                                    )

class ThreadsList(InboxView):
    """shows list of threads for a given user"""  
    template_name = 'threads_list.html'

    def get_context(self, request):
        """returns thread list data"""
        if request.method != 'GET':
            raise PermissionDenied()

        threads = Message.objects.get_threads_for_user(request.user)
        threads = threads.values('id', 'headline', 'is_read')
        return {'threads': threads}


class SendersList(InboxView):
    """shows list of senders for a user"""
    template_name = 'senders_list.html'

    def get_context(request):
        """get data about senders for the user"""
        if request.method != 'GET':
            raise PermissionDenied()

        senders = SenderList.objects.get_senders_for_user(request.user)
        senders = senders.values('id', 'username')
        return {'senders': senders}


class ThreadDetails(InboxView):
    """shows entire thread in the unfolded form"""
    template_name = 'thread_details.html'

    def get_context(request):
        """shows individual thread"""
        if request.method != 'GET':
            raise PermissionDenied()

        thread_id = IntegerField().clean(request.GET['thread_id'])
        #todo: assert that current thread is the root
        messages = Message.objects.filter(root__id=thread_id)
        messages = messages.values('html')
        return {'messages': messages}
