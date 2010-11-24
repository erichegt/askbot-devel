import hotshot
import time
import os
import datetime
import functools
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.utils import simplejson
from askbot import exceptions as askbot_exceptions
from django.core import exceptions as django_exceptions

def auto_now_timestamp(func):
    """decorator that will automatically set
    argument named timestamp to the "now" value if timestamp == None

    if there is no timestamp argument, then exception is raised
    """
    @functools.wraps(func)
    def decorated_func(*arg, **kwarg):
        timestamp = kwarg.get('timestamp', None)
        if timestamp is None:
            kwarg['timestamp'] = datetime.datetime.now()
        return func(*arg, **kwarg)
    return decorated_func


def ajax_login_required(view_func):
    @functools.wraps(view_func)
    def wrap(request,*args,**kwargs):
        if request.user.is_authenticated():
            return view_func(request,*args,**kwargs)
        else:
            json = simplejson.dumps({'login_required':True})
            return HttpResponseForbidden(json,mimetype='application/json')
    return wrap


def anonymous_forbidden(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_anonymous():
            raise askbot_exceptions.LoginRequired()
        return view_func(request, *args, **kwargs)
    return wrapper


def get_only(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'GET':
            raise django_exceptions.PermissionDenied(
                'request method %s is not supported for this function' % \
                request.method
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def post_only(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            raise django_exceptions.PermissionDenied(
                'request method %s is not supported for this function' % \
                request.method
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_only(view_func):
    @functools.wraps(view_func)
    def wrapper(request,*args,**kwargs):
        if not request.is_ajax():
            raise Http404
        try:
            data = view_func(request,*args,**kwargs)
        except Exception, e:
            message = unicode(e)
            if message == '':
                message = _('Oops, apologies - there was some error')
            logging.debug(message)
            return HttpResponse(message, status = 404, mimetype='application/json')

        if isinstance(data, HttpResponse):#is this used?
            data.mimetype = 'application/json'
            return data
        else:
            json = simplejson.dumps(data)
            return HttpResponse(json,mimetype='application/json')
    return wrapper


try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except:
    PROFILE_LOG_BASE = "/tmp"

def profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the 
    file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof', 
    where the time stamp is in UTC. This makes it easy to run and compare 
    multiple trials.     

    http://code.djangoproject.com/wiki/ProfilingDjango
    """

    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            final_log_file = base + ext

            prof = hotshot.Profile(final_log_file)
            try:
                ret = prof.runcall(f, *args, **kwargs)
            finally:
                prof.close()
            return ret

        return _inner
    return _outer
