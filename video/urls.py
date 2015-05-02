# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('video.views',
    url(r'^video/get_url/$', view='get_url'),
    url(r'^video/get_image/$', view='get_image'),
)
