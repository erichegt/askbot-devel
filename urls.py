import os.path
from django.conf.urls.defaults import *
from django.contrib import admin
from forum.views import index
from forum import views as app
from forum.feed import RssLastestQuestionsFeed
from django.utils.translation import ugettext as _

admin.autodiscover()
feeds = {
    'rss': RssLastestQuestionsFeed
}

APP_PATH = os.path.dirname(__file__)
urlpatterns = patterns('',
    (r'^$', index),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/content/images/favicon.ico'}),
    (r'^favicon\.gif$', 'django.views.generic.simple.redirect_to', {'url': '/content/images/favicon.gif'}),
    (r'^content/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH, 'templates/content').replace('\\','/')}
    ),
    (r'^%s(?P<path>.*)$' % _('upfiles/'), 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH, 'templates/upfiles').replace('\\','/')}
    ),
    (r'^%s' % _('account/'), include('django_authopenid.urls')),
    (r'^%s/$' % _('signin/'), 'django_authopenid.views.signin'),
    url(r'^%s%s$' % (_('email/'), _('change/')), 'django_authopenid.views.changeemail', name='user_changeemail'),
    url(r'^%s%s$' % (_('email/'), _('sendkey/')), 'django_authopenid.views.send_email_key'),
    url(r'^%s%s(?P<id>\d+)/(?P<key>[\dabcdef]{32})/$' % (_('email/'), _('verify/')), 'django_authopenid.views.verifyemail', name='user_verifyemail'),
    url(r'^%s$' % _('about/'), app.about, name='about'),
    url(r'^%s$' % _('faq/'), app.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), app.privacy, name='privacy'),
    url(r'^%s$' % _('logout/'), app.logout, name='logout'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('comments/')), app.answer_comments, name='answer_comments'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('edit/')), app.edit_answer, name='edit_answer'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('revisions/')), app.answer_revisions, name='answer_revisions'),
    url(r'^%s$' % _('questions/'), app.questions, name='questions'),
    url(r'^%s%s$' % (_('questions/'), _('ask/')), app.ask, name='ask'),
    url(r'^%s%s$' % (_('questions/'), _('unanswered/')), app.unanswered, name='unanswered'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('edit/')), app.edit_question, name='edit_question'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('close/')), app.close, name='close'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('reopen/')), app.reopen, name='reopen'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('answer/')), app.answer, name='answer'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('vote/')), app.vote, name='vote'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('revisions/')), app.question_revisions, name='question_revisions'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('comments/')), app.question_comments, name='question_comments'),
    url(r'^%s(?P<question_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('questions/'), _('questions/'),_('delete/')), app.delete_question_comment, name='delete_question_comment'),
    url(r'^%s(?P<answer_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('answers/'), _('answers/'),_('delete/')), app.delete_answer_comment, name='delete_answer_comment'),
    #place general question item in the end of other operations
    url(r'^%s(?P<id>\d+)//*' % _('question/'), app.question, name='question'),
    url(r'^%s$' % _('tags/'), app.tags, name='tags'),
    url(r'^%s(?P<tag>[^/]+)/$' % _('tags/'), app.tag),
    url(r'^%s$' % _('users/'),app.users, name='users'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('users/'), _('edit/')), app.edit_user, name='edit_user'),
    url(r'^%s(?P<id>\d+)//*' % _('users/'), app.user, name='user'),
    url(r'^%s$' % _('badges/'),app.badges, name='badges'),
    url(r'^%s(?P<id>\d+)//*' % _('badges/'), app.badge, name='badge'),
    url(r'^%s%s$' % (_('messages/'), _('markread/')),app.read_message, name='read_message'),
    # (r'^admin/doc/' % _('admin/doc'), include('django.contrib.admindocs.urls')),
    (r'^%s(.*)' % _('nimda/'), admin.site.root),
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^%s$' % _('upload/'), app.upload),
    url(r'^%s$' % _('books/'), app.books, name='books'),
    url(r'^%s%s(?P<short_name>[^/]+)/$' % (_('books/'), _('ask/')), app.ask_book, name='ask_book'),
    url(r'^%s(?P<short_name>[^/]+)/$' % _('books/'), app.book, name='book'),
    url(r'^%s$' % _('search/'), app.search, name='search'),
    (r'^categorias/$', app.categories),
    (r'^categorias/(?P<category>[^/]+)/$', app.category),
)
