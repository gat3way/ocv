from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sentinel.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^$', 'sentinel.views.homepage', name='homepage'),
    (r'^', include('detect.urls')),
    (r'^', include('video.urls')),
) 
