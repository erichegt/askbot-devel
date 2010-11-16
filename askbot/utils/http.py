"""http utils similar to django's but with more
specific properties
"""
import logging
from django.http import HttpResponse
from django.utils import simplejson

class JsonResponse(HttpResponse):
    """response class that receives a dictionary
    and returns it serialized with simplejson
    and response type application/json
    """
    def __init__(self, *args, **kwargs):
        mimetype = kwargs.pop('mimetype', None)
        if mimetype:
            raise KeyError('JsonResponse does not accept mimetype variable')
        kwargs['mimetype'] = 'application/json'
        string_data = simplejson.dumps(kwargs.pop('data', ''))
        super(JsonResponse, self).__init__(string_data, *args, **kwargs)

class JsonLoggingErrorResponse(JsonResponse):
    """like json response, only with empty content
    and status=500, plus logs an error message
    """ 
    def __init__(self, error, *args, **kwargs):
        status = kwargs.pop('status', None)
        if status:
            raise KeyError('JsonLoggingErrorResponse does not accept status')
        log_level = kwargs.pop('log_level', 'debug')
        assert(log_level in ('debug', 'critical'))
        log = getattr(logging, log_level)
        log('ajax error ' + unicode(error))
        kwargs['status'] = 500
        super(JsonLoggingErrorResponse, self).__init__(*args, **kwargs)
