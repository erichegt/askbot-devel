"""
askbot askbot url configuraion file
"""
import os.path
from django.conf import settings
from django.conf.urls.defaults import url, patterns, include
from django.conf.urls.defaults import handler500, handler404
from django.contrib import admin
from askbot import views
from askbot.feed import RssLastestQuestionsFeed, RssIndividualQuestionFeed
from askbot.sitemap import QuestionsSitemap
from askbot.skins.utils import update_media_revision

admin.autodiscover()
update_media_revision()#needs to be run once, so put it here

if hasattr(settings, "ASKBOT_TRANSLATE_URL") and settings.ASKBOT_TRANSLATE_URL:
    from django.utils.translation import ugettext as _
else:
    _ = lambda s:s

feeds = {
    'rss': RssLastestQuestionsFeed,
    'question':RssIndividualQuestionFeed
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
        {'document_root': os.path.join(
                settings.PROJECT_ROOT,
                'askbot',
                'upfiles'
            ).replace('\\','/')
        },
        name='uploaded_file',
    ),
    #no translation for this url!!
    url(r'import-data/$', views.writers.import_data, name='import_data'),
    url(r'^%s$' % _('about/'), views.meta.about, name='about'),
    url(r'^%s$' % _('faq/'), views.meta.faq, name='faq'),
    url(r'^%s$' % _('privacy/'), views.meta.privacy, name='privacy'),
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

    # BEGIN Questions (main page) urls. All this urls work both normally and through ajax

    url( # section/sort/query/search/tags/author
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/search:search/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/tags/author/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/tags/author/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/query/tags/author for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/author/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/author/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/query/author for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/search/author
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/search:search/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/tags/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/tags/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/query/search/tags
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/search:search/tags:(?P<tags>[\w\d\-\+\#]+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/tags for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/tags:(?P<tags>[\w\d\-\+\#]+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),

    url( # section/sort/query/search
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/search:search/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/query/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/query for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/query:(?P<query>[\w\d\-\+\#]+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/tags/author/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/tags/author/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/tags/author for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/author/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/author/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # section/sort/author for use with ajax
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/tags/page_size Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # section/sort/tags/page Note:issues with default start_over
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # include section/sort/tags
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/tags:(?P<tags>[\w\d\-\+\#]+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # tags/author/page_size Note:issues with default start_over
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # tags/author/page Note:issues with default start_over
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # include tags/author
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    
    url( # author/page_size Note:issues with default start_over
        r'^%s/author:(?P<author>\d+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # author/page Note:issues with default start_over
        r'^%s/author:(?P<author>\d+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # include author
        r'^%s/author:(?P<author>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    
    url( # tags/page_size Note:issues with default start_over
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # tags/page Note:issues with default start_over
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # include tags
        r'^%s/tags:(?P<tags>[\w\d\-\+\#]+)/$' % _('questions'), 
        views.readers.questions,
        name='questions'
    ),
    url( # include section/sort/page_size
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/page_size:(?P<page_size>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # include section/sort/page
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/page:(?P<page>\d+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # include section/sort
        r'^%s/section:(?P<scope>\w+)/sort:(?P<sort>[\w\-]+)/$' % _('questions'), 
        views.readers.questions, 
        name='questions'
    ),
    url( # removes tag, this is used only with ajax and this parameters is always used alone
        r'^%s/remove_tag:(?P<remove_tag>[\w\d\-\#]+)/$' % _('questions'),
        views.readers.questions,
        {'start_over': (None)}, # this parameter is true by default, so we are making it false here
        name='questions'
    ),
    url( # reset_query, for ajax use
        r'^%s/reset_query:(?P<reset_query>\w+)/$' % _('questions'), 
        views.readers.questions,
        {'start_over': (None)}, # this parameter is true by default, so we are making it false here
        name='questions'
    ),
    url(
        r'^%s$' % _('questions/'),
        views.readers.questions,
        name='questions'
    ),

    # END main page urls
    
    url(
        r'^api/get_questions/',
        views.commands.api_get_questions,
        name = 'api_get_questions'
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
    url(
        r'^%s%s$' % (_('widgets/'), _('questions/')),
        views.readers.widget_questions, 
        name='widget_questions'
    ),
    url(#ajax only
        r'^comment/upvote/$',
        views.commands.upvote_comment,
        name = 'upvote_comment'
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
        r'^comment/delete/$',
        views.writers.delete_comment, 
        name='delete_comment'
    ),
    url(#ajax only
        r'^comment/get_text/$',
        views.readers.get_comment, 
        name='get_comment'
    ),
    url(#ajax only
        r'^question/get_body/$',
        views.readers.get_question_body, 
        name='get_question_body'
    ),
    url(
        r'^%s$' % _('tags/'), 
        views.readers.tags, 
        name='tags'
    ),
    url(#ajax only
        r'^%s%s$' % ('mark-tag/', 'interesting/'),
        views.commands.mark_tag,
        kwargs={'reason':'good','action':'add'},
        name='mark_interesting_tag'
    ),
    url(#ajax only
        r'^%s%s$' % ('mark-tag/', 'ignored/'),
        views.commands.mark_tag,
        kwargs={'reason':'bad','action':'add'},
        name='mark_ignored_tag'
    ),
    url(#ajax only
        r'^unmark-tag/',
        views.commands.mark_tag,
        kwargs={'action':'remove'},
        name='unmark_tag'
    ),
    url(#ajax only
        r'^set-tag-filter-strategy/',
        views.commands.set_tag_filter_strategy,
        name = 'set_tag_filter_strategy'
    ),
    url(
        r'^get-tags-by-wildcard/',
        views.commands.get_tags_by_wildcard,
        name = 'get_tags_by_wildcard'
    ),
    url(
        r'^get-tag-list/',
        views.commands.get_tag_list,
        name = 'get_tag_list'
    ),
    url(
        r'^swap-question-with-answer/',
        views.commands.swap_question_with_answer,
        name = 'swap_question_with_answer'
    ),
    url(
        r'^%s$' % _('subscribe-for-tags/'),
        views.commands.subscribe_for_tags,
        name = 'subscribe_for_tags'
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
        r'^%s(?P<id>\d+)/(?P<slug>.+)/%s$' % (
            _('users/'),
            _('subscriptions/'),
        ),
        views.users.user,
        kwargs = {'tab_name': 'email_subscriptions'},
        name = 'user_subscriptions'
    ),
    url(
        r'^%s(?P<id>\d+)/(?P<slug>.+)/$' % _('users/'),
        views.users.user,
        name='user_profile'
    ),
    url(
        r'^%s$' % _('users/update_has_custom_avatar/'),
        views.users.update_has_custom_avatar,
        name='user_update_has_custom_avatar'
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
        {'domain': 'djangojs','packages': ('askbot',)},
        name = 'askbot_jsi18n'
    ),
)

if getattr(settings, 'ASKBOT_USE_STACKEXCHANGE_URLS', False):
    urlpatterns += (url(
        r'^%s(?P<id>\d+)/' % _('questions/'), 
        views.readers.question, 
        name='question'
    ),)
else:
    urlpatterns += (url(
        r'^%s(?P<id>\d+)/' % _('question/'), 
        views.readers.question, 
        name='question'
    ),)

if 'askbot.deps.django_authopenid' in settings.INSTALLED_APPS:
    urlpatterns += (
        url(r'^%s' % _('account/'), include('askbot.deps.django_authopenid.urls')),
    )

if 'avatar' in settings.INSTALLED_APPS:
    #unforturately we have to wire avatar urls here,
    #because views add and change are adapted to
    #use jinja2 templates
    urlpatterns += (
        url('^avatar/add/$', views.avatar_views.add, name='avatar_add'),
        url(
            '^avatar/change/$',
            views.avatar_views.change,
            name='avatar_change'
        ),
        url(
            '^avatar/delete/$',
            views.avatar_views.delete,
            name='avatar_delete'
        ),
        url(#this urs we inherit from the original avatar app
            '^avatar/render_primary/(?P<user_id>[\+\d]+)/(?P<size>[\d]+)/$',
            views.avatar_views.render_primary,
            name='avatar_render_primary'
        ),
    )
