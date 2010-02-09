# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext as _

urlpatterns = patterns('django_authopenid.views',
    # yadis rdf
    url(r'^yadis.xrdf$', 'xrdf', name='yadis_xrdf'),
     # manage account registration
    url(r'^%s$' % _('signin/'), 'signin', name='user_signin'),
    url(r'^%s%s$' % (_('signin/'),_('newquestion/')), 'signin', kwargs = {'newquestion':True}, name='user_signin_new_question'),
    url(r'^%s%s$' % (_('signin/'),_('newanswer/')), 'signin', kwargs = {'newanswer':True}, name='user_signin_new_answer'),
    url(r'^%s$' % _('signout/'), 'signout', name='user_signout'),
    url(r'^%s%s$' % (_('signin/'), _('complete/')), 'complete_signin', 
        name='user_complete_signin'),
    url('^%s$' % _('external-login/'),'external_legacy_login_info', name='user_external_legacy_login_issues'),
    url(r'^%s$' % _('register/'), 'register', name='user_register'),
    url(r'^%s$' % _('signup/'), 'signup', name='user_signup'),
    #disable current sendpw function
    url(r'^%s$' % _('sendpw/'), 'sendpw', name='user_sendpw'),
    url(r'^%s%s$' % (_('password/'), _('confirm/')), 'confirmchangepw', name='user_confirmchangepw'),

    # manage account settings
    url(r'^$', _('account_settings'), name='user_account_settings'),
    url(r'^%s$' % _('password/'), 'changepw', name='user_changepw'),
    url(r'^%s%s$' % (_('email/'),_('validate/')), 'changeemail', name='user_validateemail',kwargs = {'action':'validate'}),
    url(r'^%s%s$' % (_('email/'), _('change/')), 'changeemail', name='user_changeemail'),
    url(r'^%s%s$' % (_('email/'), _('sendkey/')), 'send_email_key', name='send_email_key'),
    url(r'^%s%s(?P<id>\d+)/(?P<key>[\dabcdef]{32})/$' % (_('email/'), _('verify/')), 'verifyemail', name='user_verifyemail'),
    url(r'^%s$' % _('openid/'), 'changeopenid', name='user_changeopenid'),
    url(r'^%s$' % _('delete/'), 'delete', name='user_delete'),
)
