from django.shortcuts import render
from django.http import HttpResponse
from video.models import LocalSource
from video.models import Source
import sentinel.settings.common as settings
import cv2
import os
import mmap
import numpy as np
# Create your views here.


# Get URL by camera name
def get_url(request):
    src = request.GET.get('src', None)
    if src:
        url = None
        try:
            lsrc = LocalSource.objects.get(name=src)
            url = lsrc.url
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