from django.core.management.base import BaseCommand, CommandError
from video.models import LocalSource as LocalSource
from video.models import Source as Source
from video.models import Sink as Sink
from detect.models import FaceRecognizer as FaceRecognizer
from detect.models import SmokeRecognizer as SmokeRecognizer
from detect.models import Face as Face
from action.models import log as log

from backend.ivs.facerecognition import FaceRecognizer
from backend.ivs.motiondetection import MotionDetector
from backend.ivs.smokedetection import SmokeDetector
from backend.ivs.tamper import TamperDetector

import backend.video.common as common
import backend.video.events as events
import backend.video.storage as storage


import cv2
from cv2 import cv
import sys
import os
import time
import sentinel.settings.common as settings
import atexit
import signal
import datetime
from django.utils import timezone
import threading
from Queue import Queue
import numpy as np



# Those need to be global?
gohome = False
queue = Queue(maxsize=0)



# Logging thread
def logger_thread(event_handler):
    while True:
        time.sleep(1)
        event_handler.cleanup()



# Storage thread
def storage_thread(camname,storagemanager):
    minute = -1
    pid = 0
    while True:
        pid,minute = storagemanager.switch_video(minute,pid,camname)
        time.sleep(1)




# Daemonize a single source
def daemonize(src):
    pid = os.fork()

    if pid > 0:
        return pid

    else:

        # Open camera
        frame_first,video_capture = common.open_source(src)

        # Instantiate our event and storage handlers
        event = events.EventHandler()
        storagemanager = storage.StorageManager(queue, (640,480))

        # Get the sinks
        raw,overlay,video_capture = common.get_sinks(src,video_capture,frame_first)


        # Each source has its own logger and recording thread
        t = threading.Thread(name="logger_thread",target=logger_thread, args=(event,))
        t.setDaemon(True)
        t.start()

        if src.store_archive:
            storagemanager.restart()
            t = threading.Thread(name="storage_thread",target=storage_thread, args=(src.name,storagemanager))
            t.setDaemon(True)
            t.start()



        # Close file descriptors
        os.close(sys.stdout.fileno())
        os.close(sys.stderr.fileno())


        # Cache some Source model properties
        tamper_detection = src.tamper_detection
        motion_detection = src.motion_detection
        face_recognizer = src.face_recognizer
        bottom_blank_pixels = src.bottom_blank_pixels
        top_blank_pixels = src.top_blank_pixels
        left_blank_pixels = src.left_blank_pixels
        right_blank_pixels = src.right_blank_pixels
        name = src.name
        smoke_detection = src.smoke_detector


        # Get the IVS objects
        if face_recognizer:
            facerecognizer = FaceRecognizer(Face.objects.filter(recognizer = src.face_recognizer))
        if motion_detection:
            motiondetector = MotionDetector(src.motion_threshold, src.motion_exclude)
        if smoke_detection:
            smokedetector = SmokeDetector(video_capture, src.smoke_detector.exposition, src.smoke_detector.min_threshold, src.smoke_detector.max_threshold)
        if tamper_detection:
            tamperdetector = TamperDetector()


        # Initialize data
        framenr = 0
        movement = False
        minute = -1
        orig_timestamp = datetime.datetime.now()
        e_fps = fps = 0
        gohome = False


        # Read some frames to warm up
        for a in range(0,3):
            ret, frame_first = video_capture.read()



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
                frame_first,video_capture = common.open_source(src)
                frame = frame_first


            # Resize input image to 640x480, draw the margins
            frame = common.draw_margins(frame,(640,480),top_blank_pixels,bottom_blank_pixels,left_blank_pixels,right_blank_pixels)


            # Tamper detection
            if tamper_detection:
                tamperdetector.capture(frame)
                res,fr = tamperdetector.analyze(frame)
                if res:
                    event.log("Tampering detected ", "trigger", image=fr, face=None, source=src, extra=None, frame=fr, fps=fps)


            # Smoke detection - RGB auto-tuning
            if smoke_detection:
                smokedetector.capture(frame)

            # Motion detection - frame grab
            if motion_detection:
                motiondetector.capture(frame)


            # Draw camname and date
            cv2.rectangle(frame, (0, 0), (640, 20), (0, 0, 0), -1)
            if minute!=datetime.datetime.now().minute or movement:
                sframe = frame.copy()
                cv2.putText(sframe, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
                minute = datetime.datetime.now().minute
            cv2.putText(frame, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))


            # Send raw frame to the streamer
            try:
                common.write_frame(raw,frame)
            except Exception:
                video_capture.release()
                frame_first,video_capture = common.open_source(src)


            # If we archive video, send frame to recorder (motion detection may be involved)
            if src.store_archive:
                try:
                    if not motion_detection:
                        storagemanager.write(frame)
                    else:
                        if movement:
                            storagemanager.write(frame)
                        else:
                            storagemanager.write(sframe)
                except Exception:
                    out2 = storagemanager.restart()



            # Smoke event occured - create event
            if smoke_detection:
                r,fr = smokedetector.analyze(frame)
                if r:
                    event.log("Smoke detected", "trigger", image=fr, face=None, source=src, extra=None, frame=fr, fps=fps)


            # Motion detection event occured - create event
            if motion_detection and movement:
                event.log("Movement detected", "trigger", image=mfr, face=None, source=src, extra=None, frame=mfr, fps=fps)

            # Update events
            event.update(frame)


            # Facial recognition
            if face_recognizer and framenr==3:
                facerecognizer.capture(frame)


            # Once in three frames we process face recognition/motion detection stuff
            if (framenr)==3:
                framenr = 0
                orig = frame

                # Recognition processing
                if face_recognizer:
                    r,fr = facerecognizer.analyze(frame)
                    for a in r:
                        if len(a)>0:
                            event.log(a + " detected", "trigger", image=fr, face=a, source=src, extra=None, frame=fr, fps=fps)
                        else:
                            event.log("Face detected", "trigger", image=fr, face=a, source=src, extra=None, frame=fr, fps=fps)

                # Movement detection processing
                if motion_detection:
                    movement,mfr = motiondetector.analyze(frame)


                # Write to overlay sink
                if overlay:
                    try:
                        if movement:
                            common.write_frame(overlay,mfr)
                        else:
                            common.write_frame(overlay,fr)
                    except Exception:
                        video_capture.release()
                        frame_first,video_capture = common.open_source(src)





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
                    os.killpg(pid, signal.SIGKILL)
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
