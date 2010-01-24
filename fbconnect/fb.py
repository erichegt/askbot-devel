from django.conf import settings
from time import time
from datetime import datetime
from urllib import urlopen,  urlencode

try:
    from json import load as load_json
except:
    from pjson import fread as load_json

from models import FBAssociation
import hashlib 
import logging

REST_SERVER = 'http://api.facebook.com/restserver.php'

def generate_sig(values):
    keys = []
    
    for key in sorted(values.keys()):
        keys.append(key)
        
    signature = ''.join(['%s=%s' % (key,  values[key]) for key in keys]) + settings.FB_SECRET
    return hashlib.md5(signature).hexdigest()

def check_cookies_signature(cookies):
    API_KEY = settings.FB_API_KEY
    
    values = {}
    
    for key in cookies.keys():
        if (key.startswith(API_KEY + '_')):
            values[key.replace(API_KEY + '_',  '')] = cookies[key]
    
    return generate_sig(values) == cookies[API_KEY]

def get_user_data(cookies):
    request_data = {
        'method': 'Users.getInfo',
        'api_key': settings.FB_API_KEY, 
        'call_id': time(), 
        'v': '1.0', 
        'uids': cookies[settings.FB_API_KEY + '_user'], 
        'fields': 'name,first_name,last_name',
        'format': 'json',
    }
    
    request_data['sig'] = generate_sig(request_data)
    fb_response = urlopen(REST_SERVER, urlencode(request_data))
    print(fb_response)
    return load_json(fb_response)[0]
    
    
def delete_cookies(response):
    API_KEY = settings.FB_API_KEY
    
    response.delete_cookie(API_KEY + '_user')
    response.delete_cookie(API_KEY + '_session_key')
    response.delete_cookie(API_KEY + '_expires')
    response.delete_cookie(API_KEY + '_ss')
    response.delete_cookie(API_KEY)
    response.delete_cookie('fbsetting_' + API_KEY)
    
def check_session_expiry(cookies):
    return datetime.fromtimestamp(float(cookies[settings.FB_API_KEY+'_expires'])) > datetime.now()

STATES = {
            'FIRSTTIMER': 1, 
            'SESSIONEXPIRED': 2, 
            'RETURNINGUSER': 3,
            'INVALIDSTATE': 4, 
}

def get_user_state(request):
    API_KEY = settings.FB_API_KEY
    
    if API_KEY in request.COOKIES:
        if check_cookies_signature(request.COOKIES):
            if check_session_expiry(request.COOKIES):
                try:
                    uassoc = FBAssociation.objects.get(fbuid=request.COOKIES[API_KEY + '_user'])
                    return (STATES['RETURNINGUSER'],  uassoc.user)
                except:
                    return (STATES['FIRSTTIMER'],  get_user_data(request.COOKIES))
            else:
                return (STATES['SESSIONEXPIRED'],  None)
    
    return (STATES['INVALIDSTATE'],  None)
    
