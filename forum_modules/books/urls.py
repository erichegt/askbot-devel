from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _

import views as app

urlpatterns = patterns('',
    url(r'^%s$' % _('books/'), app.books, name='books'),
    url(r'^%s%s(?P<short_name>[^/]+)/$' % (_('books/'), _('ask/')), app.ask_book, name='ask_book'),
    url(r'^%s(?P<short_name>[^/]+)/$' % _('books/'), app.book, name='book'),
)