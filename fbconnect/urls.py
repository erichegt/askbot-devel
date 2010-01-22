from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.views.generic.simple import direct_to_template
from views import signin,  register

urlpatterns = patterns('',
    url(r'^xd_receiver$',  direct_to_template,  {'template': 'fbconnect/xd_receiver.html'},  name='xd_receiver'), 
    url(r'^%s' % _('signin/'),  signin,  name="fb_signin"), 
    url(r'^%s' % _('register/'),  register,  name="fb_user_register"), 
    
)
