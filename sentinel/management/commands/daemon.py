from django.core.management.base import BaseCommand, CommandError
from video.models import LocalSource as LocalSource
from video.models import Source as Source
from video.models import Sink as Sink
from detect.models import Recognizer as Recognizer
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

        # Previous ffmpeg was there, kill it
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
                time.sleep(0.01)
                fps += 1
            fps /= 3
            fps = int(fps)
            sys.stderr.write("FPS = " + str(fps)+"\n")
            out.release
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
                time.sleep(0.01)
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




# TanTriggs stuff - unused
def extract(x,alpha,gamma,sigma0,sigma1,tau):
    x = np.array(x, dtype=np.float32)
    x = np.power(x, gamma)
    x = np.asarray(
        ndimage.gaussian_filter(x, sigma1) - ndimage.gaussian_filter(x, sigma0)
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

    x = tau * np.tanh(x / tau)
    return np.array(x, np.uint8)

def compute(x, alpha=0.05,gamma=0.4,sigma0=3,sigma1=4,tau=15.0):
        xp = []
        for xi in x:
            xp.append(extract(xi,alpha,gamma,sigma0,sigma1,tau))
        return np.array(xp)


def write_frame(dst,img):
    dst.seek(0, os.SEEK_SET)
    dst.write(img.tostring())


# Daemonize a single source
def daemonize(src):
    pid = os.fork()

    if pid > 0:
        return pid

    else:

        # Setup camera source
        if src.url.isdigit():
            video_capture = cv2.VideoCapture(int(src.url))
        else:
            video_capture = cv2.VideoCapture(src.url)
        ret, frame_first = video_capture.read()
        ret, frame_first = video_capture.read()


        # Setup mmap'ed files for raw and overlay sinks
        sink = src.overlay_sink
        if sink:
            sink_name = sink.short_id
            filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink_name)
            overlay_f = open(filename, 'w+b')
            overlay_f.seek(0, os.SEEK_SET)
            overlay_f.write(frame_first.tostring() )
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
            raw_f.write(frame_first.tostring() )
            raw_f.seek(0, os.SEEK_SET)
            raw = mmap.mmap(raw_f.fileno(), len(frame_first.tostring()), mmap.MAP_SHARED, prot=mmap.PROT_WRITE)
        else:
            raw = None

        # Setup a queue and a new pipe
        r2,w2=os.pipe()
        queue.put(r2)
        queue.put(w2)
        out2 = os.fdopen(w2,"w")

        # Each source has its own logger and recording thread
        t = threading.Thread(name="cleanup_thread",target=cleanup_thread)
        t.setDaemon(True)
        t.start()
        t = threading.Thread(name="storage_thread",target=storage_thread, args=(src.name,))
        t.setDaemon(True)
        t.start()


        # FACIAL RECOGNIZER - DO WHAT'S NEEDED!
        size = 1
        (images, lables, names, id) = ([], [], {}, 0)
        faces = Face.objects.filter(recognizer = src.recognizer)

        # Load user face models
        fn_dir = os.path.join(settings.PROJECT_ROOT,"run","models")
        for face in faces:
            if face.active:
                names[id] = face.name
                subjectpath = os.path.join(fn_dir, face.name)
                for filename in os.listdir(subjectpath):
                    path = subjectpath + '/' + filename
                    lable = id
                    images.append(cv2.imread(path, 0))
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
                    images.append(cv2.imread(path, 0))
                    lables.append(int(lable))
                id += 1


        # Prepare recognizer
        (im_width, im_height) = (112, 92)
        (images, lables) = [numpy.array(lis) for lis in [images, lables]]
        model = cv2.createFisherFaceRecognizer()
        model.setDouble("threshold",2000)
        model2 = cv2.createLBPHFaceRecognizer()
        model2.setDouble("threshold",2000)
        if len(faces) > 1:
            model.train(images, lables)
            model2.train(images, lables)

        os.close(sys.stdout.fileno())
        #os.close(sys.stderr.fileno())



        gohome = False

        faceCascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(os.path.realpath(__file__)),"haarcascade_frontalface_default.xml"))
        framenr = 0
        motion_detection = src.motion_detection
        recognizer = src.recognizer
        name = src.name
        motion_threshold = (50-src.motion_threshold)
        if motion_threshold<0:
            motion_threshold = 1
        fgbg = cv2.BackgroundSubtractorMOG2(history=3,varThreshold=motion_threshold,bShadowDetection=True)


        bottom_blank_pixels = src.bottom_blank_pixels
        top_blank_pixels = src.top_blank_pixels
        left_blank_pixels = src.left_blank_pixels
        right_blank_pixels = src.right_blank_pixels
        ret, frame_first = video_capture.read()
        movement = False
        minute = -1
        orig_timestamp = datetime.datetime.now()
        e_fps = fps = 0

        while not gohome:
            time.sleep(0.01)
            e_fps+=1
            e_time = datetime.datetime.now()
            fps = e_fps / (e_time-orig_timestamp).total_seconds()

            framenr += 1
            ret, frame = video_capture.read()
            try:
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
            except Exception:
                continue

            if motion_detection:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            cv2.rectangle(frame, (0, 0), (640, 20), (0, 0, 0), -1)
            if minute!=datetime.datetime.now().minute or movement:
                sframe = frame.copy()
                cv2.putText(sframe, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
                minute = datetime.datetime.now().minute
            cv2.putText(frame, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
            write_frame(raw,frame)

            try:
                if not motion_detection:
                    out2.write( frame.tostring() )
                else:
                    if movement:
                        out2.write( mframe.tostring() )
                    else:
                        out2.write( sframe.tostring() )
            except Exception:
                r2,w2=os.pipe()
                queue.put(r2)
                queue.put(w2)
                out2 = os.fdopen(w2,"w")

            if motion_detection and movement:
                e_log("Movement detected", "trigger", image=orig, face=None, source=src, extra=None, frame=frame, fps=fps)

            e_update(frame)

            if motion_detection:
                fgmask = fgbg.apply(gray)
                fgmask = cv2.blur(fgmask, (10, 10))
            elif recognizer and framenr==3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if (framenr)==3:
                framenr = 0
                orig = frame

                # Movement detection
                if motion_detection:
                    fgbg = cv2.BackgroundSubtractorMOG2(history=3,varThreshold=motion_threshold,bShadowDetection=True)
                    fgbg.setDouble("fVarInit",150)
                    fgbg.setDouble("fVarMin",150)
                    fgbg.setDouble("fCT",0.5)
                    fgbg.setDouble("fTau",0.5)
                    delta_count = cv2.countNonZero(fgmask)
                    if (delta_count!=0):
                        movement = True
                        cv2.putText(frame, "MOVEMENT", (565, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (20, 20, 255))
                        mframe = frame.copy()
                        contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                        cv2.drawContours(frame, contours, -1, (0,0,255), 1)
                    else:
                        movement = False


                # Recognition
                if recognizer:
                    size = 2
                    mini = cv2.resize(gray, (int(gray.shape[1] / size), int(gray.shape[0] / size)))
                    faces = faceCascade.detectMultiScale(
                        mini,
                        scaleFactor=1.1,
                        minNeighbors=15,
                        flags=0,
                        minSize=(5, 5),
                    )

                    for i in range(len(faces)):
                        face_i = faces[i]
                        (x, y, w, h) = [int(v * size) for v in face_i]
                        face = gray[y:y + h, x:x + w]
                        face_resize = cv2.resize(face, (im_width, im_height))
                        #face_resize2 = compute(face_resize)
                        face_resize2 = face_resize
                        prediction = model.predict(face_resize2)
                        if names.has_key(prediction[0]):
                            prediction2 = model2.predict(face_resize2)
                            if names.has_key(prediction2[0] and prediction2[0]==prediction[0]):
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(frame,
                                    '%s' % (names[prediction[0]]),
                                    (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1.2,(0, 255, 0))
                                # Log face!
                                e_log("Face detected", "trigger", image=orig, face=names[prediction[0]], source=src, extra=None, frame=frame, fps=fps)
                        else:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            e_log("Face detected", "trigger", image=orig, face="", source=src, extra=None, frame=frame, fps=fps)
                    write_frame(overlay,frame)




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
