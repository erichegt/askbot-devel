import os.path
from django.conf.urls.defaults import *
from django.contrib import admin
from forum import views as app
from forum.feed import RssLastestQuestionsFeed
from django.utils.translation import ugettext as _

admin.autodiscover()
feeds = {
    'rss': RssLastestQuestionsFeed
}

APP_PATH = os.path.dirname(os.path.dirname(__file__))
urlpatterns = patterns('',
    url(r'^$', app.index, name='index'),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/content/images/favicon.ico'}),
    (r'^favicon\.gif$', 'django.views.generic.simple.redirect_to', {'url': '/content/images/favicon.gif'}),
    (r'^content/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH, 'templates/content').replace('\\','/')}
    ),
    (r'^%s(?P<path>.*)$' % _('upfiles/'), 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH, 'templates/upfiles').replace('\\','/')}
    ),
    (r'^%s/$' % _('signin/'), 'django_authopenid.views.signin'),
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

    url(r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('questions/'), _('comments/'),_('delete/')), \
                                                app.delete_comment, kwargs={'commented_object_type':'question'},\
                                                name='delete_question_comment'),

    url(r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('answers/'), _('comments/'),_('delete/')), \
                                                app.delete_comment, kwargs={'commented_object_type':'answer'}, \
                                                name='delete_answer_comment'), \
    #place general question item in the end of other operations
    url(r'^%s(?P<id>\d+)//*' % _('question/'), app.question, name='question'),
    url(r'^%s$' % _('tags/'), app.tags, name='tags'),
    url(r'^%s(?P<tag>[^/]+)/$' % _('tags/'), app.tag, name='tag_questions'),
    url(r'^%s$' % _('users/'),app.users, name='users'),
    url(r'^%s(?P<id>\d+)/$' % _('moderate-user/'), app.moderate_user, name='moderate_user'),
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
    url(r'^%s$' % _('feedback/'), app.feedback, name='feedback'),
    (r'^%s' % _('account/'), include('django_authopenid.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
