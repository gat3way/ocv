# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

urlpatterns = patterns('video.views',
    url(r'^video/get_url/$', view='get_url'),
    url(r'^video/get_image/$', view='get_image'),
    url(r'^video/grid_view/$', view='grid_view'),
    url(r'^video/grid_layout_get/$', view='grid_layout_get'),
    url(r'^video/grid_layout_set/$', view='grid_layout_set'),
    url(r'^video/get_sinks/$', view='get_sinks'),
    url(r'^video/cam_pan_left$', view='cam_pan_left'),
    url(r'^video/cam_pan_right$', view='cam_pan_right'),
    url(r'^video/cam_pan_bottom_left$', view='cam_pan_bottom_left'),
    url(r'^video/cam_pan_bottom_right$', view='cam_pan_bottom_right'),
    url(r'^video/cam_pan_up_left$', view='cam_pan_up_left'),
    url(r'^video/cam_pan_up_right$', view='cam_pan_up_right'),
    url(r'^video/cam_pan_up$', view='cam_pan_up'),
    url(r'^video/cam_pan_bottom$', view='cam_pan_bottom'),
)
