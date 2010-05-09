from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.views.generic.simple import direct_to_template
from views import signin,  register

urlpatterns = patterns('',
    url(
            r'^xd_receiver$',  
            direct_to_template,  
            {'template': 'fbconnect/xd_receiver.html',},
            name='xd_receiver'
        ), 
    
    url(r'^%s$' % _('signin/'),  signin,  name="fb_signin"), 
    url(r'^%s%s$' % (_('signin/'),  _('newquestion/')),  signin, {'newquestion': True},  name="fb_signin_new_question"), 
    url(r'^%s%s$' % (_('signin/'),  _('newanswer/')),  signin, {'newanswer': True},  name="fb_signin_new_answer"), 
    
    url(r'^%s$' % _('register/'),  register,  name="fb_user_register"), 
    url(r'^%s%s$' % (_('register/'),  _('newquestion/')),  register, {'newquestion': True},  name="fb_user_register_new_question"), 
    url(r'^%s%s$' % (_('register/'),  _('newanswer/')),  register, {'newanswer': True},  name="fb_user_register_new_answer"),     
)
