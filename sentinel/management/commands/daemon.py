from django.core.management.base import BaseCommand, CommandError
from video.models import LocalSource as LocalSource
from video.models import Source as Source
from video.models import Sink as Sink
from detect.models import FaceRecognizer as FaceRecognizer
from detect.models import SmokeRecognizer as SmokeRecognizer
from detect.models import Face as Face
from action.models import log as log
import cv2
from cv2 import cv
import sys
import os
import time
import numpy
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
import numpy as np
from scipy import ndimage
import json

gohome = False
events = []
queue = Queue(maxsize=0)
camfps = {}




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
    global camfps

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


# Camera: log event
def e_log(name, e_type, image=None, face=None, source=None, extra=None,frame=None,fps=0):
    global events

    r_face = None
    r_name = name
    if face and face!="":
        r_face = Face.objects.get(name=face)
        r_name = face + " Detected"

    entry = { "name" : r_name, "e_type" : e_type, "face": r_face, "source" : source, "extra" : extra}

    found = False
    found_event = None
    for event in events:
        if entry["name"] == event["name"] and entry["e_type"] == event["e_type"] and entry["face"] == event["face"] and entry["source"] == event["source"] and entry["extra"] == event["extra"]:
            found = True
            found_event = event
            break

    if not found:
        entry["image"] = save_picture(image)
        video,recorder = record_video(source,frame,fps)
        entry["video"] = video
        entry["recorder"] = recorder
        entry["timestamp"] = datetime.datetime.now()
        event = log(None, entry["name"], entry["e_type"], image=entry["image"], face=entry["face"], source=entry["source"], comment=None, extra=entry["extra"], time_offset=0, video=entry["video"])
        entry["event"] = event
        entry["toremove"] = False
        events.append(entry)
    else:
        found_event["timestamp"] = datetime.datetime.now()


def e_update(frame):
    for event in events[:]:
        if event["recorder"]:
            write_video(event["recorder"], frame)
        if event["toremove"]:
            close_video(event["recorder"])
            events.remove(event)


def cleanup_log():
    global events

    now = datetime.datetime.now()
    for event in events[:]:
        delta = now-event["timestamp"]
        if delta.total_seconds() > 5:
            event["event"].duration_seconds = (event["timestamp"]-event["event"].timestamp).total_seconds()
            event["event"].save()
            event["toremove"] = True


def cleanup_thread():
    while True:
        time.sleep(1)
        cleanup_log()




def switch_video(minute,pid,camname):
    global camfps
    # a hour expired, save new file
    minute2 = datetime.datetime.now().minute
    pid2 = pid

    if (minute2 != minute and minute2==0) or minute == -1:
        minute = minute2

        # Kill former process
        if pid2 != 0:
            os.kill(pid, signal.SIGTERM)
        rfd = wfd = None
        rfd = queue.get()
        wfd = queue.get()


        pid3 = os.fork()
        if pid3==0:
            os.close(wfd)

            currentHour = str(datetime.datetime.now().hour)
            currentDay = str(datetime.datetime.now().day)
            currentMonth = str(datetime.datetime.now().month)
            currentYear = str(datetime.datetime.now().year)
            dname = currentYear + "_" + currentMonth + "_" + currentDay

            path = os.path.join(settings.PROJECT_ROOT,"run","storage",camname)
            if not os.path.isdir(path):
                os.mkdir(path)
            path = os.path.join(settings.PROJECT_ROOT,"run","storage",camname,dname)
            if not os.path.isdir(path):
                os.mkdir(path)
            path = os.path.join(settings.PROJECT_ROOT,"run","storage",camname,dname,currentHour + ".avi")
            if os.path.isfile(path):
                os.remove(path)


            # Estimate fps
            fourcc = cv2.cv.CV_FOURCC('F','M','P','4')
            out = cv2.VideoWriter(path, fourcc, 20, (640, 480))
            sec = datetime.datetime.now().second
            fps = 0
            buffer = []
            while len(buffer)!=640*480*3:
                buffer = os.read(rfd,640*480*3)
            while datetime.datetime.now().second == sec:
                time.sleep(0.01)
            sec = datetime.datetime.now().second
            dt = np.dtype((np.uint8, 3))
            while (datetime.datetime.now().second-sec)<3:
                buffer = os.read(rfd,640*480*3)
                while len(buffer)!=640*480*3:
                    buffer = os.read(rfd,640*480*3)
                    if len(buffer)==0:
                        out.release()
                        return pid,minute2
                img = np.fromstring(buffer, dt)
                img = np.reshape(img,(480,640,3))
                out.write(img)
                time.sleep(0.03)
                fps += 1
            fps /= 3
            fps = int(fps)
            sys.stderr.write("FPS = " + str(fps)+"\n")
            out.release()
            camfps[camname] = fps

            fourcc = cv2.cv.CV_FOURCC('F','M','P','4')
            out = cv2.VideoWriter(path, fourcc, fps, (640, 480))
            dt = np.dtype((np.uint8, 3))
            while True:
                buffer = os.read(rfd,640*480*3)
                while len(buffer)!=640*480*3:
                    buffer = os.read(rfd,640*480*3)
                    if len(buffer)==0:
                        out.release()
                        return pid,minute2
                img = np.fromstring(buffer, dt)
                img = np.reshape(img,(480,640,3))
                out.write(img)
                time.sleep(0.03)
        else:
            os.close(rfd)
            os.waitpid(pid,os.WNOHANG)
            return pid3,minute2
    else:
        return pid,minute2

def storage_thread(camname):
    minute = -1
    pid = 0
    while True:
        pid,minute = switch_video(minute,pid,camname)
        time.sleep(1)




# TanTriggs transform
def tantriggs(x, alpha=0.1,gamma=0.2,sigma0=1,sigma1=2,tau=10.0):
    x = np.array(x, dtype=np.float32)
    x = np.power(x, gamma)
    s0 = 3*sigma0
    s1 = 3*sigma1
    if ((s0%2)==0):
        s0+=1
    if ((s1%2)==0):
        s1+=1

    x = np.asarray(
        ndimage.gaussian_filter(x, sigma0) - ndimage.gaussian_filter(x, sigma1)
        )

    x = x / np.power(
        np.mean(np.power(np.abs(x), alpha)),
        1.0 / alpha
        )
    x = x / np.power(
            np.mean(
                np.power(
                    np.minimum(np.abs(x), tau),
                    alpha
                )
            ),
            1.0 / alpha
        )

    x = np.tanh(x / tau) * tau
    x = cv2.normalize(x,x,-220,0,cv2.NORM_MINMAX)
    return np.array(x, np.uint8)




def open_source(src):
    # Setup camera source
    frame_first = None
    sys.stdout.write("Retrying source!" + src.url + "\n")
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


def write_frame(dst,img):
    dst.seek(0, os.SEEK_SET)
    dst.write(img.tostring())



# Smoke detection RGB filters
def rgbfilter_gray(image, rgbthreshold):
    b,g,r = cv2.split(image)

    rd = rgbthreshold

    min1 = cv2.min(b,g)
    min1 = cv2.min(min1,r)
    max1 = cv2.max(b,g)
    max1 = cv2.max(max1,r)

    diff = cv2.absdiff(max1,min1)
    res = cv2.compare(diff,rd,cv2.CMP_LT)
    return res


def rgbfilter_black(image,image_bg):
    rd = 2
    rd2 = 100
    diff = cv2.subtract(image_bg,cv2.cvtColor(image,cv2.COLOR_BGR2GRAY))
    res = cv2.compare(diff,rd,cv2.CMP_GT)
    res1 = cv2.compare(diff,rd2,cv2.CMP_LT)
    return cv2.bitwise_and(res,res1)


def rgbfilter_white(image,image_bg):
    rd = 2
    rd2 = 100
    diff = cv2.subtract(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),image_bg)
    res = cv2.compare(diff,rd,cv2.CMP_GT)
    res1 = cv2.compare(diff,rd2,cv2.CMP_LT)
    return cv2.bitwise_and(res,res1)

def filters(image,image2,rgbthreshold):
    return cv2.threshold(cv2.bitwise_and(cv2.bitwise_or(rgbfilter_black(image,image2),rgbfilter_white(image,image2)),rgbfilter_gray(image,rgbthreshold)), 200, 255, cv2.THRESH_BINARY)





# Daemonize a single source
def daemonize(src):
    pid = os.fork()

    if pid > 0:
        return pid

    else:

        # Open camera
        frame_first,video_capture = open_source(src)

        # Setup mmap'ed files for raw and overlay sinks
        sink = src.overlay_sink
        if sink:
            sink_name = sink.short_id
            filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink_name)
            overlay_f = open(filename, 'w+b')
            overlay_f.seek(0, os.SEEK_SET)
            try:
                overlay_f.write(frame_first.tostring() )
            except Exception:
                video_capture.release()
                frame_first,video_capture = open_source(src)
            overlay_f.seek(0, os.SEEK_SET)
            overlay = mmap.mmap(overlay_f.fileno(), len(frame_first.tostring()), mmap.MAP_SHARED, prot=mmap.PROT_WRITE)
        else:
            overlay = None
        sink = src.raw_sink
        if sink:
            sink_name = sink.short_id
            filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink_name)
            raw_f = open(filename, 'w+b')
            raw_f.seek(0, os.SEEK_SET)
            try:
                raw_f.write(frame_first.tostring() )
            except Exception:
                video_capture.release()
                frame_first,video_capture = open_source(src)

            raw_f.seek(0, os.SEEK_SET)
            raw = mmap.mmap(raw_f.fileno(), len(frame_first.tostring()), mmap.MAP_SHARED, prot=mmap.PROT_WRITE)
        else:
            raw = None



        # Each source has its own logger and recording thread
        t = threading.Thread(name="cleanup_thread",target=cleanup_thread)
        t.setDaemon(True)
        t.start()
        if src.store_archive:
            # Setup a queue and a new pipe
            r2,w2=os.pipe()
            queue.put(r2)
            queue.put(w2)
            out2 = os.fdopen(w2,"w")
            # Launch store thread
            t = threading.Thread(name="storage_thread",target=storage_thread, args=(src.name,))
            t.setDaemon(True)
            t.start()


        # FACIAL RECOGNIZER - DO WHAT'S NEEDED!
        size = 1
        (images, images2, lables, names, id) = ([], [], [], {}, 0)
        faces = Face.objects.filter(recognizer = src.face_recognizer)

        # Load user face models
        fn_dir = os.path.join(settings.PROJECT_ROOT,"run","models")
        for face in faces:
            if face.active:
                names[id] = face.name
                subjectpath = os.path.join(fn_dir, face.name)
                for filename in os.listdir(subjectpath):
                    path = subjectpath + '/' + filename
                    lable = id
                    #images.append(cv2.imread(path, 0))
                    images.append(tantriggs(cv2.imread(path, 0)))
                    lables.append(int(lable))
                id += 1

        # Load default models
        fn_dir = os.path.join(settings.PROJECT_ROOT,"run","att_models")
        for (subdirs, dirs, files) in os.walk(fn_dir):
            for subdir in dirs:
                names[id] = ''
                subjectpath = os.path.join(fn_dir, subdir)
                for filename in os.listdir(subjectpath):
                    path = subjectpath + '/' + filename
                    lable = id
                    #images.append(cv2.imread(path, 0))
                    images.append(tantriggs(cv2.imread(path, 0)))
                    lables.append(int(lable))
                id += 1


        # Prepare recognizer
        (im_width, im_height) = (112, 92)
        (images, lables) = [numpy.array(lis) for lis in [images, lables]]
        model = cv2.createFisherFaceRecognizer()
        model.setDouble("threshold",2000000000)
        model2 = cv2.createLBPHFaceRecognizer()
        model2.setDouble("threshold",2000000000)
        if id > 1:
            model.train(images, lables)
            model2.train(images, lables)


        # Prepare face cascade
        faceCascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(os.path.realpath(__file__)),"haarcascade_frontalface_default.xml"))
        framenr = 0


        # Prepare motion detection
        motion_threshold = src.motion_threshold*5
        if motion_threshold<0:
            motion_threshold = 1
        fgbg = cv2.BackgroundSubtractorMOG2(history=3,varThreshold=motion_threshold,bShadowDetection=True)
        #fgbg = cv2.BackgroundSubtractorMOG2()

        # Prepare smoke detection
        if src.smoke_detector:
            detector = src.smoke_detector
            FRAMES = detector.exposition
            FRAMES_BACK=5
            MINCONTOUR=100
            THRESHOLD_GEO=20
            THRESHOLD_LOW=detector.min_threshold
            THRESHOLD_HIGH=detector.max_threshold
            THRESHOLD_RGB=10
            prevc = 0
            extents = []
            entropies = []
            points = []
            areas = []
            curs = []
            cx = []
            cy = []
            frames = []
            for a in range(0,FRAMES_BACK):
                var,s_fgmask = video_capture.read()
                s_fgmask = cv2.resize(s_fgmask, (640, 480)) 
                frames.append(cv2.cvtColor(s_fgmask,cv2.COLOR_BGR2GRAY))
            empty_src = np.zeros((s_fgmask.shape[0],s_fgmask.shape[1],1), np.uint8)
            empty_srcmask = np.zeros((s_fgmask.shape[0],s_fgmask.shape[1],1), np.uint8)

            bground = frames.pop(0)
            bground2 = empty_src
            imagepixels = s_fgmask.shape[0]*s_fgmask.shape[1]
            fn = 0



        # Close file descriptors
        #os.close(sys.stdout.fileno())
        #os.close(sys.stderr.fileno())


        # Cache some Source model properties
        motion_detection = src.motion_detection
        face_recognizer = src.face_recognizer
        bottom_blank_pixels = src.bottom_blank_pixels
        top_blank_pixels = src.top_blank_pixels
        left_blank_pixels = src.left_blank_pixels
        right_blank_pixels = src.right_blank_pixels
        name = src.name
        smoke_detector = src.smoke_detector
        try:
            regions = json.loads(src.motion_exclude)
        except Exception:
            regions = { 'rects' : [] }



        # Initialize data
        movement = False
        minute = -1
        orig_timestamp = datetime.datetime.now()
        e_fps = fps = 0
        gohome = False

        # Read some frames to warm up
        ret, frame_first = video_capture.read()
        ret, frame_first = video_capture.read()
        ret, frame_first = video_capture.read()
        fgmask = frame_first



        # Main loop
        while not gohome:

            # Do not hog the CPU
            time.sleep(0.03)

            # FPS estimation
            e_fps+=1
            e_time = datetime.datetime.now()
            fps = int(e_fps / (e_time-orig_timestamp).total_seconds())

            # Read a frame, retries if error
            framenr += 1
            ret, frame = video_capture.read()
            if not ret:
                frame_first,video_capture = open_source(src)
                frame = frame_first


            # Resize input image to 640x480, draw the margins
            if frame.shape[1]!=640 or frame.shape[0]!=480:
                frame = cv2.resize(frame, (640,480))
            if top_blank_pixels>0:
                cv2.rectangle(frame, (0, 0), (640, top_blank_pixels), (0, 0, 0), -1)
            if bottom_blank_pixels>0:
                cv2.rectangle(frame, (0, 480-bottom_blank_pixels), (640, 480), (0, 0, 0), -1)
            if left_blank_pixels>0:
                cv2.rectangle(frame, (0, 0), (480, left_blank_pixels), (0, 0, 0), -1)
            if right_blank_pixels>0:
                cv2.rectangle(frame, (640-right_blank_pixels,0), (640, 480), (0, 0, 0), -1)


            # Face recognizer - keep a grayscale version of the image
            if face_recognizer:
                frame_orig = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)



            # Smoke detection - RGB auto-tuning
            if smoke_detector:
                fn += 1
                if (fn%60)==0:
                    r,img2 = cv2.threshold(rgbfilter_gray(frame,THRESHOLD_RGB),THRESHOLD_RGB, 255, cv2.THRESH_BINARY)
                    r = (cv2.countNonZero(img2)*100)/ (frame.shape[0]*frame.shape[1])
                    if (r<20):
                        if THRESHOLD_RGB<50:
                            THRESHOLD_RGB += 1
                    elif (r>30):
                        if THRESHOLD_RGB>1:
                            THRESHOLD_RGB -= 1

                # Smoke detection processing here
                imgbg = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                imgbg = cv2.equalizeHist(imgbg)
                r,mask = filters(frame,bground,THRESHOLD_RGB)
                mask1 = cv2.bitwise_and(imgbg,mask)
                mask2 = cv2.bitwise_and(bground,mask)

                frames.append(imgbg)

                s_fgmask = cv2.absdiff(mask1,mask2)
                r,fgmask1 = cv2.threshold(s_fgmask, THRESHOLD_HIGH, 255, cv2.THRESH_BINARY_INV)
                r,fgmask2 = cv2.threshold(s_fgmask, THRESHOLD_LOW, 255, cv2.THRESH_BINARY)
                s_fgmask = cv2.bitwise_and(fgmask1,fgmask2)
                res = imgbg

                contours, hierarchy = cv2.findContours(s_fgmask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)

                contours2 = []
                extents_t = []
                entropies_t = []
                areas_t = []
                points_t = []
                cx_t = []
                cy_t = []

                extents_n = []
                entropies_n = []
                areas_n = []
                points_n = []
                quality_n = []
                index_n = []
                curs_n = []
                cx_n = []
                cy_n = []

                nowc = 0
                # Get data on our contours
                bground2 = bground

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    nowc+=area
                    if area > MINCONTOUR:
                        empty = empty_src.copy()
                        cv2.drawContours(empty, cnt, -1, (255), -1)

                        res1 = cv2.bitwise_and(bground2,empty)
                        r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)
                        #print msk

                        hist_img = cv2.calcHist([res1],[0],msk,[256],[0,256])
                        hist_img /= area
                        bgmax = hist_img.max()
                        lhist = cv2.log(hist_img)
                        hist_img = (lhist*hist_img)
                        entropy_bg = -(hist_img.sum())

                        res1 = res
                        res1 = cv2.bitwise_and(res1,empty)
                        r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)

                        hist = cv2.calcHist([res1],[0],msk,[256],[0,256])
                        hist  /= area
                        fgmax = hist.max()
                        lhist = cv2.log(hist)
                        hist = (lhist*hist)
                        entropy_fg = -(hist.sum())

                        res1 = cv2.absdiff(res,bground2)
                        res1 = cv2.bitwise_and(res1,empty)
                        r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)

                        hist2 = cv2.calcHist([res1],[0],msk,[256],[0,256])
                        hist2  /= area
                        fgmax = hist2.max()
                        lhist = cv2.log(hist2)
                        hist2 = (lhist*hist2)
                        entropy_diff = -(hist2.sum())

                        if (entropy_diff<entropy_fg and entropy_diff<entropy_bg):
                            contours2.append(cnt)
                            points_t.append(len(cnt))
                            (x,y,w,h) = cv2.boundingRect(cnt)

                            entropies_t.append((entropy_bg,entropy_fg,entropy_diff))
                            extents_t.append((x,y,w,h))
                            areas_t.append(area)
                            M = cv2.moments(cnt)
                            cx_t.append(int(M['m10']/M['m00']))
                            cy_t.append(int(M['m01']/M['m00']))

                if nowc>(((frame.shape[0]*frame.shape[1])*2)/3) and prevc!=0:
                    for a in range(0,FRAMES_BACK):
                        frames.pop(0)
                        frames.append(mask1)
                    extents_t = []
                    entropies_t = []
                    points_t = []
                    areas_t = []
                    curs_t = []
                    cx_t = []
                    cy_t = []
                    extents = []
                    entropies = []
                    points = []
                    areas = []
                    curs = []
                    cx = []
                    cy = []
                    prevc = nowc
                prevc = nowc

                for a in range(0,len(cx)):
                    found = False
                    for b in range(0,len(cx_t[:])):
                        if not found and cx_t[b]>=0 and curs[a]>=0 and ((abs(cx[a]-cx_t[b])<THRESHOLD_GEO/2 and abs(cy[a]-cy_t[b])<THRESHOLD_GEO/2) or (abs(cx[a]-cx_t[b])<THRESHOLD_GEO and abs(cy[a]-cy_t[b])<THRESHOLD_GEO)):
                            if ((areas[a]!=areas_t[b] or (extents_t[b]!=extents[a])) or points[a]!=points_t[b]) \
                            and abs(entropies_t[b][2]-entropies[a][2])<min(entropies_t[b][2],entropies[a][2]):
                                index_n.append(b)
                                extents_n.append(extents_t[b])
                                areas_n.append(areas_t[b])
                                points_n.append(points_t[b])
                                entropies_n.append(entropies_t[b])
                                cx_n.append(cx_t[b])
                                cy_n.append(cy_t[b])

                                #if curs[a]>=(FRAMES)/2:
                                #    print fn,entropies_t[b],entropies[a],curs[a]
                                curs_n.append(curs[a]+1)

                            extents_t[b] = -200
                            areas_t[b] = -200
                            points_t[b] = -200
                            cx_t[b] = -200
                            cy_t[b] = -200
                            found = True

                # Get new ones
                for a in range(0,len(extents_t)):
                    if extents_t[a]>=0 and areas_t[a]>=0 and points_t[a]>0:
                        curs_n.append(0)
                        extents_n.append(extents_t[a])
                        areas_n.append(areas_t[a])
                        points_n.append(points_t[a])
                        entropies_n.append((entropies_t[a][0],entropies_t[a][1],entropies_t[a][2]))
                        index_n.append(a)
                        cx_n.append(cx_t[a])
                        cy_n.append(cy_t[a])

                # Copy over the new frames
                extents = extents_n[:]
                entropies = entropies_n[:]
                areas = areas_n[:]
                points = points_n[:]
                curs = curs_n[:]
                cx = cx_n[:]
                cy = cy_n[:]



            # For motion detection we work with scaled down image to save some CPU cycles
            if motion_detection:
                gray = cv2.resize(frame, (int(frame.shape[1] / 2), int(frame.shape[0] / 2)))
                gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

            # Draw camname and date
            cv2.rectangle(frame, (0, 0), (640, 20), (0, 0, 0), -1)
            if minute!=datetime.datetime.now().minute or movement:
                sframe = frame.copy()
                cv2.putText(sframe, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
                minute = datetime.datetime.now().minute
            cv2.putText(frame, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))


            # Send raw frame to the streamer
            try:
                write_frame(raw,frame)
            except Exception:
                video_capture.release()
                frame_first,video_capture = open_source(src)

            # If we archive video, send frame to recorder (motion detection may be involved)
            if src.store_archive:
                try:
                    if not motion_detection:
                        out2.write( frame.tostring() )
                    else:
                        if movement:
                            out2.write( frame.tostring() )
                        else:
                            out2.write( sframe.tostring() )
                except Exception:
                    r2,w2=os.pipe()
                    queue.put(r2)
                    queue.put(w2)
                    out2 = os.fdopen(w2,"w")



            # Smoke event occured - create event
            if smoke_detector:
                r = 0
                for a in range(0,len(curs)):
                    if curs[a]>=FRAMES:
                        cv2.drawContours(frame, contours2, index_n[a], (0,0,255), -1)
                        r += 1
                if r>0:
                    e_log("Smoke detected", "trigger", image=frame, face=None, source=src, extra=None, frame=frame, fps=fps)
                bground = frames.pop(0)


            # Motion detection event occured - create event
            if motion_detection and movement:
                e_log("Movement detected", "trigger", image=orig, face=None, source=src, extra=None, frame=frame, fps=fps)

            # Update events
            e_update(frame)


            # Motion detection - do the calculations excluding the red areas
            if motion_detection:
                gray2 = gray.copy()
                for rect in regions["rects"]:
                    x1 = rect["x"]
                    y1 = rect["y"]
                    x2 = rect["w"]+x1
                    y2 = rect["h"]+y1
                    cv2.rectangle(gray2, (x1/2, y1/2), (x2/2, y2/2), (0, 0, 0), -1)
                fgmask = fgbg.apply(gray2,fgmask,0.1)
                fgmask = cv2.blur(fgmask, (10, 10))
            # Face recognition needs a grayscale version each 3 frames
            elif face_recognizer and framenr==3:
                gray = cv2.resize(frame, (int(frame.shape[1] / 2), int(frame.shape[0] / 2)))
                gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)


            # Once in three frames we process face recognition/motion detection stuff
            if (framenr)==3:
                framenr = 0
                orig = frame

                # Movement detection processing
                if motion_detection:
                    delta_count = cv2.countNonZero(fgmask)
                    if (delta_count!=0):
                        movement = True
                        cv2.putText(frame, "MOVEMENT", (565, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (20, 20, 255))
                        fgmask = cv2.resize(fgmask, (int(fgmask.shape[1] * 2), int(fgmask.shape[0] * 2)))
                        contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                        cv2.drawContours(frame, contours, -1, (0,0,255), 1)
                    else:
                        movement = False


                # Recognition processing
                if face_recognizer:
                    size = 1
                    mini = gray
                    faces = faceCascade.detectMultiScale(
                        mini,
                        scaleFactor=1.4,
                        minNeighbors=4,
                        flags=0,
                        minSize=(5, 5),
                    )

                    for i in range(len(faces)):
                        size = 2
                        face_i = faces[i]
                        (x, y, w, h) = [int(v * size) for v in face_i]
                        face = frame_orig[y:y + h, x:x + w]
                        face_resize = cv2.resize(face, (im_width, im_height))
                        face_resize2 = tantriggs(face_resize)
                        prediction = model.predict(face_resize2)
                        if names.has_key(prediction[0]):
                            prediction2 = model2.predict(face_resize2)
                            if names.has_key(prediction2[0]) and prediction2[0]==prediction[0]:
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(frame,
                                    '%s' % (names[prediction[0]]),
                                    (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1.2,(0, 255, 0))
                                # Log face!
                                e_log("Face detected", "trigger", image=orig, face=names[prediction[0]], source=src, extra=None, frame=frame, fps=fps)
                            else:
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                e_log("Face detected", "trigger", image=orig, face="", source=src, extra=None, frame=frame, fps=fps)
                        else:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            e_log("Face detected", "trigger", image=orig, face="", source=src, extra=None, frame=frame, fps=fps)




                # Write to overlay sink
                if overlay:
                    try:
                        write_frame(overlay,frame)
                    except Exception:
                        video_capture.release()
                        frame_first,video_capture = open_source(src)





class Command(BaseCommand):
    help = 'Does the real job behind the scenes'
    args = '<command...>'

    def delpid(self):
        try:
            os.remove(self.pidfile)
        except Exception:
            pass

    def get_pid(self):
        self.pidfile = os.path.join(settings.PROJECT_ROOT, "sentinel.pid")
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid


    def stop(self):
        pid = self.get_pid()

        if not pid:
            message = "pidfile %s does not exist. Not running?\n"
            sys.stderr.write(message % self.pidfile)
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            return
        try:
            i = 0
            while 1:
                os.killpg(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1
                if i % 10 == 0:
                    os.killpg(pid, signal.SIGHUP)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def start(self):
        self.stdout.write('Starting daemon...\n')
        self.pidfile = os.path.join(settings.PROJECT_ROOT, "sentinel.pid")
        pid = str(os.getpgrp())
        file(self.pidfile, 'w+').write("%s\n" % pid)

        pids = []
        for src in Source.objects.all():
            if src.active:
                self.stdout.write('Source: ' + src.name + "url: " + src.url+"\n")
                pid = daemonize(src)
                pids.append(pid)


        for pid in pids:
            os.waitpid(pid,0)

        while not gohome:
            time.sleep(1)


    def handle(self, *args, **options):
        if len(args)!=1:
            self.stdout.write('Bad command (start/stop/restart expected)')
            return

        arg = args[0]
        if arg == "start":
            print "start"
            self.start()
        elif arg == "stop":
            print "stop"
            self.stop()
        elif arg == "restart":
            print "restart"
            self.stop()
            self.start()
        else:
            self.stdout.write('Bad command (start/stop/restart expected)')
