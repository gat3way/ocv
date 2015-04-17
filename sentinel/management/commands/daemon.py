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
gohome = False
events = []
queue = Queue(maxsize=0)



# Generate configuration file for ffserver
def prepare_config_file():
    conf_file = open("/tmp/ffserver.conf","w")
    header = """
Port 8090
BindAddress 0.0.0.0
MaxHTTPConnections 2000
MaxClients 1000
MaxBandwidth 1000000
CustomLog -

"""
    conf_file.write(header)
    for src in Source.objects.all():
        sink = src.raw_sink
        raw_name = sink.short_id
        sink = src.overlay_sink
        overlay_name = sink.short_id
        conf_file.write("<Feed " + raw_name + ".ffm>\n")
        conf_file.write("File /tmp/" + raw_name + ".ffm\n")
        conf_file.write("FileMaxSize 1M\n")
        #conf_file.write("ACL allow 127.0.0.1\n")
        conf_file.write("</Feed>\n")
        conf_file.write("<Feed " + overlay_name + ".ffm>\n")
        conf_file.write("File /tmp/" + overlay_name + ".ffm\n")
        conf_file.write("FileMaxSize 1M\n")
        conf_file.write("ACL allow 127.0.0.1\n")
        conf_file.write("</Feed>\n")

    for src in Source.objects.all():
        sink = src.raw_sink
        if sink:
            raw_name = sink.short_id
            conf_file.write("<stream " + raw_name + ".swf>\n")
            conf_file.write("Feed " + raw_name + ".ffm\n")
            conf_file.write("Format swf\n")
            conf_file.write("VideoFrameRate 20\n")
            conf_file.write("VideoBitRate 1024\n")
            conf_file.write("VideoQMin 1\n")
            conf_file.write("VideoQMax 25\n")
            conf_file.write("VideoSize 640x480\n")
            conf_file.write("NoAudio\n")
            conf_file.write("</stream>\n")
            conf_file.write("<stream small_" + overlay_name + ".swf>\n")
            conf_file.write("Feed " + overlay_name + ".ffm\n")
            conf_file.write("Format swf\n")
            conf_file.write("VideoFrameRate 20\n")
            conf_file.write("VideoBitRate 1024\n")
            conf_file.write("VideoQMin 1\n")
            conf_file.write("VideoQMax 25\n")
            conf_file.write("VideoSize 426x320\n")
            conf_file.write("NoAudio\n")
            conf_file.write("</stream>\n")

        sink = src.overlay_sink
        if sink:
            overlay_name = sink.short_id
            conf_file.write("<stream small_" + raw_name + ".swf>\n")
            conf_file.write("Feed " + raw_name + ".ffm\n")
            conf_file.write("Format swf\n")
            conf_file.write("VideoFrameRate 20\n")
            conf_file.write("VideoBitRate 1024\n")
            conf_file.write("VideoQMin 1\n")
            conf_file.write("VideoQMax 25\n")
            conf_file.write("VideoSize 426x320\n")
            conf_file.write("NoAudio\n")
            conf_file.write("</stream>\n")
            conf_file.write("<stream " + overlay_name + ".swf>\n")
            conf_file.write("Feed " + overlay_name + ".ffm\n")
            conf_file.write("Format swf\n")
            conf_file.write("VideoFrameRate 20\n")
            conf_file.write("VideoBitRate 1024\n")
            conf_file.write("VideoQMin 1\n")
            conf_file.write("VideoQMax 25\n")
            conf_file.write("VideoSize 640x480\n")
            conf_file.write("NoAudio\n")
            conf_file.write("</stream>\n")

    conf_file.close()


# Start ffserver
def start_ffserver():
    pid = os.fork()
    if pid == 0:
        pid = os.fork()
        if pid == 0:
            os.close(sys.stdout.fileno())
            os.close(sys.stderr.fileno())
            os.execl("/usr/local/bin/ffserver", "ffserver", "-f", "/tmp/ffserver.conf")
        else:
            os.wait()
            sys.exit(0)
    else:
        return



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

    #retval,encoded = cv2.imencode(".png", image)
    cv2.imwrite(path, image)
    return d1+"/"+d2+"/"+fln+".png"

# Camera: log event
def e_log(name, e_type, image=None, face=None, source=None, extra=None):
    global events

    r_face = None
    r_name = name
    if face and face!="":
        r_face = Face.objects.get(name=face)
        r_name = face + " Detected"

    entry = { "name" : r_name, "e_type" : e_type, "face": r_face, "source" : source, "extra" : extra}

    found = False
    for event in events:
        if entry["name"] == event["name"] and entry["e_type"] == event["e_type"] and entry["face"] == event["face"] and entry["source"] == event["source"] and entry["extra"] == event["extra"]:
            found = True
            break

    if not found:
        entry["image"] = save_picture(image)
        entry["timestamp"] = datetime.datetime.now()
        events.append(entry)
        #sys.stderr.write("LOGGING: " + str(entry))


def cleanup_log():
    global events

    #sys.stderr.write("!!!" + str(events))
    now = datetime.datetime.now()
    for event in events[:]:
        delta =  now-event["timestamp"]
        if delta.total_seconds() > 10:
            log(None, event["name"], event["e_type"], image=event["image"], face=event["face"], source=event["source"], comment=None, extra=event["extra"], time_offset=-10)
            events.remove(event)


def cleanup_thread():
    while True:
        time.sleep(1)
        cleanup_log()




def switch_video(minute,pid,camname):
    # a hour expired, save new file
    minute2 = datetime.datetime.now().minute
    pid2 = pid
    if (minute2 != minute and minute2==0) or minute == -1:
        minute = minute2
        rfd = wfd = None
        while (not rfd) and (not wfd):
            rfd = queue.get()
            wfd = queue.get()
            time.sleep(1)

        pid3 = os.fork()
        if pid3==0:
            sys.stderr.write("RFD="+str(rfd)+" WFD="+str(wfd))
            # Previous ffmpeg was there, kill it
            if pid2 != 0:
                os.kill(pid, signal.SIGTERM)
            os.close(wfd)
            os.dup2(rfd,sys.stdin.fileno())
            os.close(sys.stdout.fileno())
            os.close(sys.stderr.fileno())

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
            path = os.path.join(settings.PROJECT_ROOT,"run","storage",camname,dname,currentHour + ".mp4")
            if os.path.isfile(path):
                os.remove(path)

            os.execl("/usr/local/bin/ffmpeg", "ffmpeg", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "640x480", "-r", "7", "-i", "-", "-an", "-f", "mp4", "-r", "7", "-an", "-s", "640x480", "-movflags", "frag_keyframe+empty_moov", "-g", "52", "-pix_fmt", "yuv420p", "-vcodec", "libx264", path)
        else:
            os.close(rfd)
            return pid3,minute2
    else:
        return pid,minute2

def storage_thread(camname):
    minute = -1
    pid = 0
    while True:
        pid,minute = switch_video(minute,pid,camname)
        time.sleep(1)



# Daemonize a single source
def daemonize(src):
    pid = os.fork()

    if pid > 0:
        return pid
    else:
        r,w=os.pipe()
        r1,w1=os.pipe()
        pid = os.fork()

        # Client: ffmpeg
        if pid == 0:
            sink = src.raw_sink
            sink_name = sink.short_id
            os.close(w)
            os.close(w1)
            os.close(r1)
            os.dup2(r,sys.stdin.fileno())
            ermsg = open("/dev/null","w")
            os.close(sys.stdout.fileno())
            os.close(sys.stderr.fileno())
            os.dup2(ermsg.fileno(),sys.stdout.fileno())
            os.dup2(ermsg.fileno(),sys.stderr.fileno())
            os.execl("/usr/local/bin/ffmpeg", "ffmpeg", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "640x480",  "-r",  "20", "-i",  "-", "-an", "http://localhost:8090/" + sink_name + ".ffm")
        # Server: we do a trick here, write to stderr and pipe it to a second ffmpeg for overlay
        else:
            pid = os.fork()
            if pid == 0:
                sink = src.overlay_sink
                sink_name = sink.short_id
                os.close(w)
                os.close(w1)
                os.close(r)

                os.dup2(r1,sys.stdin.fileno())
                ermsg = open("/dev/null","w")
                os.close(sys.stdout.fileno())
                os.close(sys.stderr.fileno())
                os.dup2(ermsg.fileno(),sys.stdout.fileno())
                os.dup2(ermsg.fileno(),sys.stderr.fileno())
                os.execl("/usr/local/bin/ffmpeg", "ffmpeg", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "640x480",  "-r",  "5", "-i",  "-", "-an", "http://localhost:8090/" + sink_name + ".ffm")
            else:
                # Setup a queue and a new pipe
                r2,w2=os.pipe()
                queue.put(r2)
                queue.put(w2)
                out2 = os.fdopen(w2,"w")


                # Each source has its own logger thread
                t = threading.Thread(name="cleanup_thread",target=cleanup_thread)
                t.setDaemon(True)
                t.start()

                # Each source has its own recording thread
                t = threading.Thread(name="storage_thread",target=storage_thread, args=(src.name,))
                t.setDaemon(True)
                t.start()


                # FACIAL RECOGNIZER - DO WHAT'S NEEDED!
                size = 1
                (images, lables, names, id) = ([], [], {}, 0)
                faces = Face.objects.filter(recognizer = src.recognizer)

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


                os.close(r)
                os.close(r1)
                os.close(sys.stdout.fileno())
                #os.close(sys.stderr.fileno())

                os.dup2(w,sys.stdout.fileno())
                out = os.fdopen(w1,"w")



                if src.url.isdigit():
                    video_capture = cv2.VideoCapture(int(src.url))
                else:
                    video_capture = cv2.VideoCapture(src.url)
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

                while not gohome:
                    framenr += 1
                    ret, frame = video_capture.read()

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

                    if motion_detection:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    cv2.rectangle(frame, (0, 0), (640, 20), (0, 0, 0), -1)
                    if minute!=datetime.datetime.now().minute or movement:
                            sframe = frame.copy()
                            cv2.putText(sframe, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
                            minute = datetime.datetime.now().minute

                    cv2.putText(frame, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))
                    sys.stdout.write(frame.tostring())
                    if not motion_detection:
                        try:
                            out2.write( frame.tostring() )
                        except Exception:
                            r2,w2=os.pipe()
                            queue.put(r2)
                            queue.put(w2)
                            out2 = os.fdopen(w2,"w")


                    if motion_detection:
                        fgmask = fgbg.apply(gray)
                        fgmask = cv2.blur(fgmask, (10, 10))
                    elif recognizer and framenr==3:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    if (framenr)==3:
                        framenr = 0
                        #orig = frame.copy()
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
                                try:
                                    out2.write( frame.tostring() )
                                except Exception:
                                    r2,w2=os.pipe()
                                    queue.put(r2)
                                    queue.put(w2)
                                    out2 = os.fdopen(w2,"w")

                                contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                                cv2.drawContours(frame, contours, -1, (0,0,255), 1)
                                # Log movement!
                                e_log("Movement detected", "trigger", image=orig, face=None, source=src, extra=None)
                            else:
                                movement = False
                                try:
                                    out2.write( sframe.tostring() )
                                except Exception:
                                    r2,w2=os.pipe()
                                    queue.put(r2)
                                    queue.put(w2)
                                    out2 = os.fdopen(w2,"w")


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
                                prediction = model.predict(face_resize)
                                if names.has_key(prediction[0]):
                                    prediction2 = model2.predict(face_resize)
                                    if names.has_key(prediction2[0] and prediction2[0]==prediction[0]):
                                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                        cv2.putText(frame,
                                            '%s' % (names[prediction[0]]),
                                            (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1.2,(0, 255, 0))
                                        # Log face!
                                        e_log("Face detected", "trigger", image=orig, face=names[prediction[0]], source=src, extra=None)
                                else:
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                    e_log("Face detected", "trigger", image=orig, face="", source=src, extra=None)

                        out.write( frame.tostring() )

                os.wait()



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

        prepare_config_file()
        start_ffserver()
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
