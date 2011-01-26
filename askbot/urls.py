"""
askbot askbot url configuraion file
"""
import os.path
from django.conf.urls.defaults import url, patterns, include
from django.conf.urls.defaults import handler500, handler404
from django.contrib import admin
from askbot import views
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
    url(r'^$', views.readers.index, name='index'),
    url(
        r'^sitemap.xml$', 
        'django.contrib.sitemaps.views.sitemap', 
        {'sitemaps': sitemaps}, 
        name='sitemap'
    ),
    url(
        r'^m/(?P<skin>[^/]+)/media/(?P<resource>.*)$', 
        views.meta.media,
        name='askbot_media',
    ),
    url(
        r'^%s(?P<path>.*)$' % settings.ASKBOT_UPLOADED_FILES_URL, 
        'django.views.static.serve',
        {'document_root': os.path.join(settings.PROJECT_ROOT, 'askbot', 'upfiles').replace('\\','/')},
        name='uploaded_file',
    ),
    #no translation for this url!!
    url(r'import-data/$', views.writers.import_data, name='import_data'),
    url(r'^%s$' % _('about/'), views.meta.about, name='about'),
    url(r'^%s$' % _('faq/'), views.meta.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), views.meta.privacy, name='privacy'),
    url(r'^%s$' % _('logout/'), views.meta.logout, name='logout'),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('edit/')), 
        views.writers.edit_answer, 
        name='edit_answer'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('answers/'), _('revisions/')), 
        views.readers.revisions, 
        kwargs = {'object_name': 'Answer'},
        name='answer_revisions'
    ),
    url(#this url works both normally and through ajax
        r'^%s$' % _('questions/'), 
        views.readers.questions, 
        name='questions'
    ),
    url(
        r'^%s%s$' % (_('questions/'), _('ask/')), 
        views.writers.ask, 
        name='ask'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('edit/')), 
        views.writers.edit_question, 
        name='edit_question'
    ),
    url(#this url is both regular and ajax
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('retag/')), 
        views.writers.retag_question, 
        name='retag_question'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('close/')), 
        views.commands.close, 
        name='close'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('reopen/')), 
        views.commands.reopen, 
        name='reopen'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('answer/')), 
        views.writers.answer, 
        name='answer'
    ),
    url(#ajax only
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('vote/')), 
        views.commands.vote, 
        name='vote'
    ),
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('questions/'), _('revisions/')), 
        views.readers.revisions, 
        kwargs = {'object_name': 'Question'},
        name='question_revisions'
    ),
    url(#ajax only
        r'^post_comments/$',
        views.writers.post_comments, 
        name='post_comments'
    ),
    url(#ajax only
        r'^edit_comment/$',
        views.writers.edit_comment,
        name='edit_comment'
    ),
    url(#ajax only
        r'^%s$' % _('command/'), 
        views.commands.ajax_command, 
        name='call_ajax'
    ),
    url(#ajax only
        r'^comment/delete/$',
        views.writers.delete_comment, 
        name='delete_comment'
    ),
    url(#ajax only
        r'^comment/get_text/$',
        views.readers.get_comment, 
        name='get_comment'
    ),
    #place general question item in the end of other operations
    url(
        r'^%s(?P<id>\d+)/' % _('question/'), 
        views.readers.question, 
        name='question'
    ),
    url(
        r'^%s$' % _('tags/'), 
        views.readers.tags, 
        name='tags'
    ),
    url(#ajax only
        r'^%s%s$' % (_('mark-tag/'),_('interesting/')),
        views.commands.mark_tag,
        kwargs={'reason':'good','action':'add'},
        name='mark_interesting_tag'
    ),
    url(#ajax only
        r'^%s%s$' % (_('mark-tag/'),_('ignored/')),
        views.commands.mark_tag,
        kwargs={'reason':'bad','action':'add'},
        name='mark_ignored_tag'
    ),
    url(#ajax only
        _('unmark-tag/'),
        views.commands.mark_tag,
        kwargs={'action':'remove'},
        name='unmark_tag'
    ),
    url(
        r'^%s$' % _('users/'),
        views.users.users, 
        name='users'
    ),
    #todo: rename as user_edit, b/c that's how template is named
    url(
        r'^%s(?P<id>\d+)/%s$' % (_('users/'), _('edit/')),
        views.users.edit_user,
        name='edit_user'
    ),
    url(
        r'^%s(?P<id>\d+)/(?P<slug>.+)/$' % _('users/'),
        views.users.user,
        name='user_profile'
    ),
    url(
        r'^%s$' % _('badges/'),
        views.meta.badges,
        name='badges'
    ),
    url(
        r'^%s(?P<id>\d+)//*' % _('badges/'),
        views.meta.badge,
        name='badge'
    ),
    url(#ajax only
        r'^%s%s$' % (_('messages/'), _('markread/')),
        views.commands.read_message,
        name='read_message'
    ),
    url(#ajax only
        r'^manage_inbox/$',
        views.commands.manage_inbox,
        name='manage_inbox'
    ),
    url(
        r'^feeds/(?P<url>.*)/$', 
        'django.contrib.syndication.views.feed',
        {'feed_dict': feeds},
        name='feeds'
    ),
    #upload url is ajax only
    url( r'^%s$' % _('upload/'), views.writers.upload, name='upload'),
    url(r'^%s$' % _('feedback/'), views.meta.feedback, name='feedback'),
    (r'^%s' % _('account/'), include('askbot.deps.django_authopenid.urls')),
    #url(r'^feeds/rss/$', RssLastestQuestionsFeed, name="latest_questions_feed"),
    url(
        r'^doc/(?P<path>.*)$', 
        'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH,'doc','build','html').replace('\\','/')},
        name='askbot_docs',
    ),
    url(
        '^custom\.css$',
        views.meta.config_variable,
        kwargs = {
            'variable_name': 'CUSTOM_CSS',
            'mimetype': 'text/css'
        },
        name = 'custom_css'
    ),
    url(
        '^custom\.js$',
        views.meta.config_variable,
        kwargs = {
            'variable_name': 'CUSTOM_JS',
            'mimetype': 'text/javascript'
        },
        name = 'custom_js'
    ),
    url(
        r'^jsi18n/$',
        'django.views.i18n.javascript_catalog',
        {'packages': ('askbot',)},
        name = 'askbot_jsi18n'
    ),
)
