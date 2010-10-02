"""
askbot askbot url configuraion file
"""
import os.path
from django.conf.urls.defaults import url, patterns, include
from django.conf.urls.defaults import handler500, handler404
from django.contrib import admin
from askbot import views as app
from askbot.feed import RssLastestQuestionsFeed
from askbot.sitemap import QuestionsSitemap
from django.utils.translation import ugettext as _
from django.conf import settings

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
    url(
        r'^sitemap.xml$', 
        'django.contrib.sitemaps.views.sitemap', 
        {'sitemaps': sitemaps}, 
        name='sitemap'
    ),
    url(
        r'^m/(?P<path>.*)$', 
        'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'skins').replace('\\','/')},
        name='askbot_media',
    ),
    url(
        r'^%s(?P<path>.*)$' % settings.ASKBOT_UPLOADED_FILES_URL, 
        'django.views.static.serve',
        {'document_root': os.path.join(settings.PROJECT_ROOT, 'askbot', 'upfiles').replace('\\','/')},
        name='uploaded_file',
    ),
    url(r'^%s$' % _('about/'), app.meta.about, name='about'),
    url(r'^%s$' % _('faq/'), app.meta.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), app.meta.privacy, name='privacy'),
    url(r'^%s$' % _('logout/'), app.meta.logout, name='logout'),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('comments/')), 
        app.writers.answer_comments, 
        name='answer_comments'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('edit/')), 
        app.writers.edit_answer, 
        name='edit_answer'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('revisions/')), 
        app.readers.revisions, 
        kwargs = {'object_name': 'Answer'},
        name='answer_revisions'
    ),
    url(
        r'^%s$' % _('questions/'), 
        app.readers.questions, 
        name='questions'
    ),
    url(
        r'^%s%s$' % (_('questions/'), _('ask/')), 
        app.writers.ask, 
        name='ask'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('edit/')), 
        app.writers.edit_question, 
        name='edit_question'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('retag/')), 
        app.writers.retag_question, 
        name='retag_question'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('close/')), 
        app.commands.close, 
        name='close'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('reopen/')), 
        app.commands.reopen, 
        name='reopen'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('answer/')), 
        app.writers.answer, 
        name='answer'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('vote/')), 
        app.commands.vote, 
        name='vote'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('revisions/')), 
        app.readers.revisions, 
        kwargs = {'object_name': 'Question'},
        name='question_revisions'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('comments/')), 
        app.writers.question_comments, 
        name='question_comments'
    ),
    url(
        r'^%s$' % _('command/'), 
        app.commands.ajax_command, 
        name='call_ajax'
    ),
    url(
        r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$'\
            % (_('questions/'), _('comments/'),_('delete/')), 
        app.writers.delete_comment, 
        kwargs={'commented_object_type':'question'}, 
        name='delete_question_comment'
    ),
    url(
        r'^%s(?P<object_id>\d+)/%s(?P<comment_id>\d+)/%s$'\
        % (_('answers/'), _('comments/'),_('delete/')), 
        app.writers.delete_comment, 
        kwargs={'commented_object_type':'answer'}, 
        name='delete_answer_comment'
    ),
    #place general question item in the end of other operations
    url(
        r'^%s(?P<id>\d+)/' % _('question/'), 
        app.readers.question, 
        name='question'
    ),
    url(
        r'^%s$' % _('tags/'), 
        app.readers.tags, 
        name='tags'
    ),
    url(
        r'^%s%s(?P<tag>[^/]+)/$' % (_('mark-tag/'),_('interesting/')),
        app.commands.mark_tag,
        kwargs={'reason':'good','action':'add'},
        name='mark_interesting_tag'
    ),
    url(
        r'^%s%s(?P<tag>[^/]+)/$' % (_('mark-tag/'),_('ignored/')),
        app.commands.mark_tag,
        kwargs={'reason':'bad','action':'add'},
        name='mark_ignored_tag'
    ),
    url(
        r'^%s(?P<tag>[^/]+)/$' % _('unmark-tag/'),
        app.commands.mark_tag,
        kwargs={'action':'remove'},
        name='mark_ignored_tag'
    ),
    url(
        r'^%s$' % _('users/'),
        app.users.users, 
        name='users'
    ),
    #todo: rename as user_edit, b/c that's how template is named
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('users/'), _('edit/')),
        app.users.edit_user,
        name='edit_user'
    ),
    url(
        r'^%s(?P<id>\d+)/(?P<slug>.+)/$' % _('users/'),
        app.users.user,
        name='user_profile'
    ),
    url(
        r'^%s$' % _('badges/'),
        app.meta.badges,
        name='badges'
    ),
    url(
        r'^%s(?P<id>\d+)//*' % _('badges/'),
        app.meta.badge,
        name='badge'
    ),
    url(
        r'^%s%s$' % (_('messages/'), _('markread/')),
        app.commands.read_message,
        name='read_message'
    ),
    url(
        r'^feeds/(?P<url>.*)/$', 
        'django.contrib.syndication.views.feed',
        {'feed_dict': feeds},
        name='feeds'
    ),
    url( r'^%s$' % _('upload/'), app.writers.upload, name='upload'),
    url(r'^%s$' % _('search/'), app.readers.search, name='search'),
    url(r'^%s$' % _('feedback/'), app.meta.feedback, name='feedback'),
    (r'^%s' % _('account/'), include('askbot.deps.django_authopenid.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
    #url(r'^feeds/rss/$', RssLastestQuestionsFeed, name="latest_questions_feed"),
    url(
        r'^doc/(?P<path>.*)$', 
        'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'doc','build','html').replace('\\','/')},
        name='askbot_docs',
    ),
)
