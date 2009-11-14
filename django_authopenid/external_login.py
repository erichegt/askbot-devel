#this file contains stub functions that can be extended to support
#connect legacy login with external site
import settings
from django_authopenid.models import ExternalLoginData
import httplib
import urllib
import Cookie
import cookielib
from django import forms
import xml.dom.minidom as xml
import logging

def login(request,user):
    """performs the additional external login operation
    """
    pass

def set_login_cookies(response,user):
    #should be unique value by design
    try:
        eld = ExternalLoginData.objects.get(user=user)

        data = eld.external_session_data
        dom = xml.parseString(data)
        login_response = dom.getElementsByTagName('login')[0]
        userid = login_response.getAttribute('lguserid') 
        username = login_response.getAttribute('lgusername')
        token = login_response.getAttribute('lgtoken')
        prefix = login_response.getAttribute('cookieprefix').decode('utf-8')
        sessionid = login_response.getAttribute('sessionid')

        c = {}
        c[prefix + 'UserName'] = username
        c[prefix + 'UserID'] = userid
        c[prefix + 'Token'] = token
        c[prefix + '_session'] = sessionid

        #custom code that copies cookies from external site
        #not sure how to set paths and domain of cookies here
        for key in c:
            if c[key]:
                response.set_cookie(str(key),value=str(c[key]))
    except ExternalLoginData.DoesNotExist:
        #this must be an OpenID login
        pass

#function to perform external logout, if needed
def logout(request):
    pass

#should raise User.DoesNotExist or pass
def clean_username(username):
    return username

def check_password(username,password):
    """connects to external site and submits username/password pair
    return True or False depending on correctness of login
    saves remote unique id and remote session data in table ExternalLoginData
    may raise forms.ValidationError
    """
    host = settings.EXTERNAL_LEGACY_LOGIN_HOST
    port = settings.EXTERNAL_LEGACY_LOGIN_PORT
    ext_site = httplib.HTTPConnection(host,port)

    #custom code. this one does authentication through
    #MediaWiki API
    params = urllib.urlencode({'action':'login','format':'xml',
            'lgname':username,'lgpassword':password})
    headers = {"Content-type": "application/x-www-form-urlencoded",
                'User-Agent':"User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7",
              "Accept": "text/xml"}
    ext_site.request("POST","/wiki/api.php",params,headers)
    response = ext_site.getresponse()
    if response.status != 200:
        raise forms.ValidationError('error ' + response.status + ' ' + response.reason)
    data = response.read().strip()
    ext_site.close()

    dom = xml.parseString(data)
    login = dom.getElementsByTagName('login')[0]
    result = login.getAttribute('result')
    
    if result == 'Success':
        username = login.getAttribute('lgusername')
        try:
            eld = ExternalLoginData.objects.get(external_username=username)
        except ExternalLoginData.DoesNotExist:
            eld = ExternalLoginData()
        eld.external_username = username
        eld.external_session_data = data
        eld.save()
        return True 
    else:
        error = login.getAttribute('details')
        raise forms.ValidationError(error)
    return False 

def createuser(username,email,password):
    pass

#retrieve email address
def get_email(username,password):
    return ''
