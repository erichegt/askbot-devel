"""semi-views for the `group_messaging` application
These are not really views - rather context generator
functions, to be used separately, when needed.

For example, some other application can call these
in order to render messages within the page.

Notice that :mod:`urls` module decorates all these functions
and turns them into complete views
"""
import copy
import datetime
from coffin.template.loader import get_template
from django.contrib.auth.models import User
from django.forms import IntegerField
from django.http import HttpResponse
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseForbidden
from django.utils import simplejson
from group_messaging.models import Message
from group_messaging.models import SenderList
from group_messaging.models import LastVisitTime
from group_messaging.models import get_personal_group_by_user_id
from group_messaging.models import get_personal_groups_for_users

class InboxView(object):
    """custom class-based view
    to be used for pjax use and for generation
    of content in the traditional way, where
    the only the :method:`get_context` would be used.
    """
    template_name = None #used only for the "GET" method
    http_method_names = ('GET', 'POST')

    def render_to_response(self, context, template_name=None):
        """like a django's shortcut, except will use
        template_name from self, if `template_name` is not given.
        Also, response is packaged as json with an html fragment
        for the pjax consumption
        """
        if template_name is None:
            template_name = self.template_name
        template = get_template(self.template_name)
        html = template.render(context)
        json = simplejson.dumps({'html': html})
        return HttpResponse(json, mimetype='application/json')
            

    def get(self, request, *args, **kwargs):
        """view function for the "GET" method"""
        context = self.get_context(request, *args, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """view function for the "POST" method"""
        pass

    def dispatch(self, request, *args, **kwargs):
        """checks that the current request method is allowed
        and calls the corresponding view function"""
        if request.method not in self.http_method_names:
            return HttpResponseNotAllowed()
        view_func = getattr(self, request.method.lower())
        return view_func(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        """Returns the context dictionary for the "get"
        method only"""
        return {}

    def as_view(self):
        """returns the view function - for the urls.py"""
        def view_function(request, *args, **kwargs):
            """the actual view function"""
            if request.user.is_authenticated() and request.is_ajax():
                view_method = getattr(self, request.method.lower())
                return view_method(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()

        return view_function


class NewThread(InboxView):
    """view for creation of new thread"""
    http_method_list = ('POST',)

    def post(self, request):
        """creates a new thread on behalf of the user
        response is blank, because on the client side we just 
        need to go back to the thread listing view whose
        content should be cached in the client'
        """
        usernames = request.POST['to_usernames']
        usernames = map(lambda v: v.strip(), usernames.split(','))
        users = User.objects.filter(username__in=usernames)

        missing = copy.copy(usernames)
        for user in users:
            if user.username in missing:
                missing.remove(user.username)

        result = dict()
        if missing:
            result['success'] = False
            result['missing_users'] = missing
        else:
            recipients = get_personal_groups_for_users(users)
            message = Message.objects.create_thread(
                            sender=request.user,
                            recipients=recipients,
                            text=request.POST['text']
                        )
            result['success'] = True
            result['message_id'] = message.id
        return HttpResponse(simplejson.dumps(result), mimetype='application/json')


class NewResponse(InboxView):
    """view to create a new response"""
    http_method_list = ('POST',)

    def post(self, request):
        parent_id = IntegerField().clean(request.POST['parent_id'])
        parent = Message.objects.get(id=parent_id)
        message = Message.objects.create_response(
                                        sender=request.user,
                                        text=request.POST['text'],
                                        parent=parent
                                    )
        return self.render_to_response(
            {'message': message}, template_name='stored_message.htmtl'
        )

class ThreadsList(InboxView):
    """shows list of threads for a given user"""  
    template_name = 'threads_list.html'
    http_method_list = ('GET',)

    def get_context(self, request):
        """returns thread list data"""
        #get threads and the last visit time
        threads = Message.objects.get_threads_for_user(request.user)
        try:
            last_visit = LastVisitTime.objects.get(user=request.user)
        except LastVisitTime.DoesNotExist:
            timestamp = datetime.datetime(2010, 3, 24)#day of askbot
            last_visit = LastVisitTime(user=request.user, at=timestamp)


        #for each thread we need to know if there is something
        #unread for the user - to mark "new" threads as bold
        threads_data = dict()
        for thread in threads:
            thread_data = dict()
            #determine status
            status = 'seen'
            if thread.last_active_at > last_visit.at:
                status = 'new'
            thread_data['status'] = status
            #determine the senders info
            senders_names = thread.senders_info.split(',')
            if request.user.username in senders_names:
                senders_names.remove(request.user.username)
            thread_data['senders_info'] = ', '.join(senders_names)
            threads_data[thread.id] = thread_data

        #after we have all the data - update the last visit time
        last_visit.at = datetime.datetime.now()
        last_visit.save()
            
        return {'threads': threads, 'threads_data': threads_data}


class SendersList(InboxView):
    """shows list of senders for a user"""
    template_name = 'senders_list.html'
    http_method_names = ('GET',)

    def get_context(self, request):
        """get data about senders for the user"""
        senders = SenderList.objects.get_senders_for_user(request.user)
        senders = senders.values('id', 'username')
        return {'senders': senders}


class ThreadDetails(InboxView):
    """shows entire thread in the unfolded form"""
    template_name = 'thread_details.html'
    http_method_names = ('GET',)

    def get_context(self, request):
        """shows individual thread"""
        thread_id = IntegerField().clean(request.GET['thread_id'])
        #todo: assert that current thread is the root
        messages = Message.objects.filter(root__id=thread_id)
        messages = messages.values('html')
        return {'messages': messages}
