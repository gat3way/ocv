#!/usr/bin/env python

import cv2
from cv2 import cv
import sys
import os
import time
import numpy as np
import sentinel.settings.common as settings
import atexit
import signal
import datetime
from django.utils import timezone
import threading
import hashlib
import random
from Queue import Queue
import mmap
from scipy import ndimage
import json




# Generate image
def save_picture(image):
    fln = str(datetime.datetime.now()) + str(int(random.random()*65535))
    m = hashlib.md5()
    m.update(fln)
    fln = str(m.hexdigest())
    d1 = str(fln[0:2])
    d2 = str(fln[2:4])

    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1)
    if not os.path.isdir(path):
        os.mkdir(path)
    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1,d2)
    if not os.path.isdir(path):
        os.mkdir(path)
    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1,d2,fln+".png")
    cv2.imwrite(path, image)
    return d1+"/"+d2+"/"+fln+".png"


# Generate video
def record_video(source,image,fps):

    fln = str(datetime.datetime.now()) + str(int(random.random()*65535))
    m = hashlib.md5()
    m.update(fln)
    fln = str(m.hexdigest())
    d1 = str(fln[0:2])
    d2 = str(fln[2:4])

    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1)
    if not os.path.isdir(path):
        os.mkdir(path)
    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1,d2)
    if not os.path.isdir(path):
        os.mkdir(path)
    path = os.path.join(settings.PROJECT_ROOT,"run","snapshots",d1,d2,fln+".avi")

    if fps<1:
        e_fps=10
    else:
        e_fps = fps

    try:
        fourcc = cv2.cv.CV_FOURCC('F','M','P','4')
        video = cv2.VideoWriter(path, fourcc, e_fps, (640, 480))
    except Exception:
        pass
    return d1+"/"+d2+"/"+fln+".avi", video


# Write video frame
def write_video(video,image):
    try:
        video.write(image)
    except Exception:
        pass




# Close video
def close_video(video):
    try:
        video.release()
    except Exception:
        pass



# Setup camera source
def open_source(src):
    frame_first = None
    sys.stdout.write("Trying source" + src.url + "\n")
    while frame_first is None:
        if src.url.isdigit():
            video_capture = cv2.VideoCapture(int(src.url))
        else:
            video_capture = cv2.VideoCapture(src.url)
        try:
            ret, frame_first = video_capture.read()
            ret, frame_first = video_capture.read()
            a = frame_first[10]
        except Exception:
            video_capture = None
        time.sleep(1)
    sys.stdout.write("Reopened source!\n")
    return frame_first,video_capture


# Write a frame
def write_frame(dst,img):
    dst.seek(0, os.SEEK_SET)
    dst.write(img.tostring())


# Gives us overlay and raw file descriptors to write frames to
def get_sinks(src,video_capture,frame):
    sink = src.overlay_sink
    if sink:
        sink_name = sink.short_id
        filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink_name)
        overlay_f = open(filename, 'w+b')
        overlay_f.seek(0, os.SEEK_SET)
        try:
            overlay_f.write(frame.tostring() )
        except Exception:
            video_capture.release()
            frame,video_capture = open_source(src)
        overlay_f.seek(0, os.SEEK_SET)
        overlay = mmap.mmap(overlay_f.fileno(), len(frame.tostring()), mmap.MAP_SHARED, prot=mmap.PROT_WRITE)
    else:
        overlay = None

    sink = src.raw_sink
    if sink:
        sink_name = sink.short_id
        filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink_name)
        raw_f = open(filename, 'w+b')
        raw_f.seek(0, os.SEEK_SET)
        try:
            raw_f.write(frame.tostring() )
        except Exception:
            video_capture.release()
            frame,video_capture = open_source(src)

        raw_f.seek(0, os.SEEK_SET)
        raw = mmap.mmap(raw_f.fileno(), len(frame.tostring()), mmap.MAP_SHARED, prot=mmap.PROT_WRITE)
    else:
        raw = None

    return raw,overlay,video_capture



# Draw black margins on image
def draw_margins(frame,resolution,top_blank_pixels,bottom_blank_pixels,left_blank_pixels,right_blank_pixels):
    if frame.shape[1]!=resolution[0] or frame.shape[0]!=resolution[1]:
        frame = cv2.resize(frame, resolution)
    if top_blank_pixels>0:
        cv2.rectangle(frame, (0, 0), (resolution[0], top_blank_pixels), (0, 0, 0), -1)
    if bottom_blank_pixels>0:
        cv2.rectangle(frame, (0, resolution[1]-bottom_blank_pixels), resolution, (0, 0, 0), -1)
    if left_blank_pixels>0:
        cv2.rectangle(frame, (0, 0), (resolution[1], left_blank_pixels), (0, 0, 0), -1)
    if right_blank_pixels>0:
        cv2.rectangle(frame, (resolution[0]-right_blank_pixels,0), resolution, (0, 0, 0), -1)

    return frame


