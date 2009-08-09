import os.path
from django.conf.urls.defaults import *
from django.contrib import admin
from forum.views import index
from forum import views as app
from forum.feed import RssLastestQuestionsFeed

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
    (r'^upfiles/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(APP_PATH, 'templates/upfiles').replace('\\','/')}
    ),
    (r'^cuenta/', include('django_authopenid.urls')),
    (r'^signin/$', 'django_authopenid.views.signin'),
    url(r'^sobre/$', app.about, name='about'),
    url(r'^faq/$', app.faq, name='faq'),
    url(r'^privacidad/$', app.privacy, name='privacy'),
    url(r'^logout/$', app.logout, name='logout'),
    url(r'^respuestas/(?P<id>\d+)/comentarios/$', app.answer_comments, name='answer_comments'),
    url(r'^respuestas/(?P<id>\d+)/editar/$', app.edit_answer, name='edit_answer'),
    url(r'^respuestas/(?P<id>\d+)/revisiones/$', app.answer_revisions, name='answer_revisions'),
    url(r'^preguntas/$', app.questions, name='questions'),
    url(r'^preguntas/preguntar/$', app.ask, name='ask'),
    url(r'^preguntas/sin-responder/$', app.unanswered, name='unanswered'),
    url(r'^preguntas/(?P<id>\d+)/editar/$', app.edit_question, name='edit_question'),
    url(r'^preguntas/(?P<id>\d+)/cerrar/$', app.close, name='close'),
    url(r'^preguntas/(?P<id>\d+)/reabrir/$', app.reopen, name='reopen'),
    url(r'^preguntas/(?P<id>\d+)/responder/$', app.answer, name='answer'),
    url(r'^preguntas/(?P<id>\d+)/votar/$', app.vote, name='vote'),
    url(r'^preguntas/(?P<id>\d+)/revisiones/$', app.question_revisions, name='question_revisions'),
    url(r'^preguntas/(?P<id>\d+)/comentarios/$', app.question_comments, name='question_comments'),
    url(r'^preguntas/(?P<question_id>\d+)/comentarios/(?P<comment_id>\d+)/borrar/$', app.delete_question_comment, name='delete_question_comment'),
    url(r'^respuestas/(?P<answer_id>\d+)/comentarios/(?P<comment_id>\d+)/borrar/$', app.delete_answer_comment, name='delete_answer_comment'),
    #place general question item in the end of other operations
    url(r'^preguntas/(?P<id>\d+)//*', app.question, name='question'),
    (r'^etiquetas/$', app.tags),
    (r'^etiquetas/(?P<tag>[^/]+)/$', app.tag),
    (r'^categorias/$', app.categories),
    (r'^categorias/(?P<category>[^/]+)/$', app.category),
    (r'^usuarios/$',app.users),
    url(r'^usuarios/(?P<id>\d+)/editar/$', app.edit_user, name='edit_user'),
    url(r'^usuarios/(?P<id>\d+)//*', app.user, name='user'),
    url(r'^distinciones/$',app.badges, name='badges'),
    url(r'^distinciones/(?P<id>\d+)//*', app.badge, name='badge'),
    url(r'^mensajes/marcarleido/$',app.read_message, name='read_message'),
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^nimda/(.*)', admin.site.root),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^upload/$', app.upload),
    url(r'^books/$', app.books, name='books'),
    url(r'^books/ask/(?P<short_name>[^/]+)/$', app.ask_book, name='ask_book'),
    url(r'^books/(?P<short_name>[^/]+)/$', app.book, name='book'),
    url(r'^buscar/$', app.search, name='search'),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
