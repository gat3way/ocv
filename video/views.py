from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse
from video.models import LocalSource
from video.models import Source
from video.models import Sink
import sentinel.settings.common as settings
import cv2
import os
import mmap
import numpy as np
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import json
import socket
import urllib2
from video.utils import request_get_url, request_post_url, get_localsource

# Create your views here.


# Get URL by camera name
def get_url(request):
    src = request.GET.get('src', None)
    if src:
        url = None
        try:
            lsrc = LocalSource.objects.get(name=src)
            url = lsrc.videourl
        except Exception:
            url = ""
        if url:
            return HttpResponse(url)
        else:
            return HttpResponse("")
    else:
        return HttpResponse("")


# Get image by url
def get_image(request):
    url = request.GET.get('url', None)
    if url:
        # Try to get existing source first
        try:
            src = Source.objects.get(url=url)
        except Exception:
            src = None

        # No existing source or not active? Try to open and get one frame
        if not src or src.active == False:
            try:
                if url.isdigit():
                    video_capture = cv2.VideoCapture(int(url))
                else:
                    video_capture = cv2.VideoCapture(url)
                ret, frame = video_capture.read()
                if frame.shape[1]!=640 or frame.shape[0]!=480:
                    frame = cv2.resize(frame, (640,480))
                r,buf=cv2.imencode(".jpg",frame)
                JpegData=buf.tostring()
                video_capture.release()
            except Exception:
                video_capture.release()
                return HttpResponse("")
            return HttpResponse(JpegData, content_type="image/png")

        # Source exists and is active? Grab frame from mmapped file
        else:
            try:
                sink = src.raw_sink
                filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink.short_id)
                if not os.path.isfile(filename):
                    return HttpResponse("")

                size = os.path.getsize(filename)
                f = open(filename, 'r')
                m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                capture = m
                capture.seek(0, os.SEEK_SET)
                dt = np.dtype((np.uint8, 3))
                img = np.fromstring(capture.read(size), dt)
                img = np.reshape(img,(480,640,3))
                r,buf=cv2.imencode(".jpg",img)
                JpegData=buf.tostring()
                f.close()
            except Exception:
                return HttpResponse("")

            return HttpResponse(JpegData, content_type="image/png")

    else:
        return HttpResponse("")


# Get image by url
def grid_view(request):
    return render_to_response('video/gridview.html',
                         {},
                         context_instance=RequestContext(request))



# Get grid layout
def grid_layout_get(request):
    layout = request.session.get('grid_layout', False)
    if layout:
        return HttpResponse(layout)
    else:
        # Initial widgets
        # TODO: setup initial value (dbsettings?)
        initial = { "widgets" : [] }
        for a in range(0,24):
            initial["widgets"].append({"h":1,"w":1,"sink":""})
        return HttpResponse(json.dumps(initial))

# Set grid layout
@csrf_exempt
def grid_layout_set(request):
    layout = request.body
    if layout:
        # TODO: json validation
        request.session['grid_layout']=layout
    return HttpResponse("")


# Get json list of sinks
def get_sinks(request):
    sinks = Sink.objects.all()
    sinkdata = { "names": [] }
    for sink in sinks:
        sinkdata["names"].append(sink.name)
    return HttpResponse(json.dumps(sinkdata))



##### PAN TILT ZOOM CONTROLS ######




def cam_pan_right(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    step = request.GET.get('step', None)
    localsource = get_localsource(src,srctype)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_right, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_right, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")



def cam_pan_left(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    localsource = get_localsource(src,srctype)
    step = request.GET.get('step', None)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_left, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_left, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")



def cam_pan_up(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    step = request.GET.get('step', None)
    localsource = get_localsource(src,srctype)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_up, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_up, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")



def cam_pan_bottom(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    localsource = get_localsource(src,srctype)
    step = request.GET.get('step', None)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_bottom, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_bottom, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")




def cam_pan_bottom_left(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    localsource = get_localsource(src,srctype)
    step = request.GET.get('step', None)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_bottom_left, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_bottom_left, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")


def cam_pan_bottom_right(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    localsource = get_localsource(src,srctype)
    step = request.GET.get('step', None)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_bottom_right, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_bottom_right, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")



def cam_pan_up_left(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    step = request.GET.get('step', None)
    localsource = get_localsource(src,srctype)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_up_left, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_up_left, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")


def cam_pan_up_right(request):
    socket.setdefaulttimeout(10)

    src = request.GET.get('src', None)
    srctype = request.GET.get('srctype', None)
    step = request.GET.get('step', None)
    localsource = get_localsource(src,srctype)

    if localsource and localsource.ptz_right:
        if localsource.ptz_control=="post":
            res = request_post_url(localsource.ptz_up_right, localsource.url, str(step), localsource.username, localsource.password, localsource.ptz_right_data)
            return HttpResponse(res)
        elif localsource.ptz_control=="get":
            res = request_get_url(localsource.ptz_up_right, localsource.url, str(step), localsource.username, localsource.password)
            return HttpResponse(res)
        else:
            return HttpResponse("unknown method")
    else:
        return HttpResponse("No url")
