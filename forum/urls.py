import os.path
from django.conf.urls.defaults import *
from django.contrib import admin
from forum import views as app
from forum.feed import RssLastestQuestionsFeed
from forum.sitemap import QuestionsSitemap
from django.utils.translation import ugettext as _
import logging

admin.autodiscover()
feeds = {
    'rss': RssLastestQuestionsFeed
}
sitemaps = {
    'questions': QuestionsSitemap
}

APP_PATH = os.path.dirname(__file__)
urlpatterns = patterns('',
    url(r'^$', app.readers.index, name='index'),
    url(r'^sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}, name='sitemap'),
    #(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),
    #(r'^favicon\.gif$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.gif'}),
    url(r'^m/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'skins').replace('\\','/')},
        name='osqa_media',
    ),
    url(r'^%s(?P<path>.*)$' % _('upfiles/'), 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'upfiles').replace('\\','/')},
        name='uploaded_file',
    ),
    url(r'^%s/$' % _('signin/'), 'django_authopenid.views.signin', name='signin'),
    url(r'^%s$' % _('about/'), app.meta.about, name='about'),
    url(r'^%s$' % _('faq/'), app.meta.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), app.meta.privacy, name='privacy'),
    url(r'^%s$' % _('logout/'), app.meta.logout, name='logout'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('comments/')), app.writers.answer_comments, name='answer_comments'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('edit/')), app.writers.edit_answer, name='edit_answer'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('revisions/')), app.readers.answer_revisions, name='answer_revisions'),
    url(r'^%s$' % _('questions/'), app.readers.questions, name='questions'),
    url(r'^%s%s$' % (_('questions/'), _('ask/')), app.writers.ask, name='ask'),
    url(r'^%s%s$' % (_('questions/'), _('unanswered/')), app.readers.unanswered, name='unanswered'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('edit/')), app.writers.edit_question, name='edit_question'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('close/')), app.commands.close, name='close'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('reopen/')), app.commands.reopen, name='reopen'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('answer/')), app.writers.answer, name='answer'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('vote/')), app.commands.vote, name='vote'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('revisions/')), app.readers.question_revisions, name='question_revisions'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('comments/')), app.writers.question_comments, name='question_comments'),
    url(r'^%s$' % _('command/'), app.commands.ajax_command, name='call_ajax'),

    url(r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('questions/'), _('comments/'),_('delete/')), \
                                                app.writers.delete_comment, kwargs={'commented_object_type':'question'},\
                                                name='delete_question_comment'),

    url(r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$' % (_('answers/'), _('comments/'),_('delete/')), \
                                                app.writers.delete_comment, kwargs={'commented_object_type':'answer'}, \
                                                name='delete_answer_comment'), \
    #place general question item in the end of other operations
    url(r'^%s(?P<id>\d+)/' % _('question/'), app.readers.question, name='question'),
    url(r'^%s$' % _('tags/'), app.readers.tags, name='tags'),
    url(r'^%s(?P<tag>[^/]+)/$' % _('tags/'), app.readers.tag, name='tag_questions'),

    url(r'^%s%s(?P<tag>[^/]+)/$' % (_('mark-tag/'),_('interesting/')), app.commands.mark_tag, \
                                kwargs={'reason':'good','action':'add'}, \
                                name='mark_interesting_tag'),

    url(r'^%s%s(?P<tag>[^/]+)/$' % (_('mark-tag/'),_('ignored/')), app.commands.mark_tag, \
                                kwargs={'reason':'bad','action':'add'}, \
                                name='mark_ignored_tag'),

    url(r'^%s(?P<tag>[^/]+)/$' % _('unmark-tag/'), app.commands.mark_tag, \
                                kwargs={'action':'remove'}, \
                                name='mark_ignored_tag'),

    url(r'^%s$' % _('users/'),app.users.users, name='users'),
    url(r'^%s(?P<id>\d+)/$' % _('moderate-user/'), app.users.moderate_user, name='moderate_user'),
    url(r'^%s(?P<id>\d+)/%s$' % (_('users/'), _('edit/')), app.users.edit_user, name='edit_user'),
    url(r'^%s(?P<id>\d+)//*' % _('users/'), app.users.user, name='user'),
    url(r'^%s$' % _('badges/'),app.meta.badges, name='badges'),
    url(r'^%s(?P<id>\d+)//*' % _('badges/'), app.meta.badge, name='badge'),
    url(r'^%s%s$' % (_('messages/'), _('markread/')),app.commands.read_message, name='read_message'),
    # (r'^admin/doc/' % _('admin/doc'), include('django.contrib.admindocs.urls')),
    url(r'^%s(.*)' % _('nimda/'), admin.site.root, name='osqa_admin'),
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name='feeds'),
    url(r'^%s$' % _('upload/'), app.writers.upload, name='upload'),
    #url(r'^%s$' % _('books/'), app.books.books, name='books'),
    #url(r'^%s%s(?P<short_name>[^/]+)/$' % (_('books/'), _('ask/')), app.books.ask_book, name='ask_book'),
    #url(r'^%s(?P<short_name>[^/]+)/$' % _('books/'), app.books.book, name='book'),
    url(r'^%s$' % _('search/'), app.readers.search, name='search'),
    url(r'^%s$' % _('feedback/'), app.meta.feedback, name='feedback'),
    (r'^%sfb/' % _('account/'),  include('fbconnect.urls')), 
    (r'^%s' % _('account/'), include('django_authopenid.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
