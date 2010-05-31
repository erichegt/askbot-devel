"""
main url configuration file for the askbot site
"""
from django.conf.urls.defaults import patterns, include, handler404, handler500
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^%s' % settings.FORUM_SCRIPT_ALIAS, include('forum.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^settings/', include('livesettings.urls')),
)

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
                    url(r'^rosetta/', include('rosetta.urls')),
                )
