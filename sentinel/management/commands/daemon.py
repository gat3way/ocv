from django.core.management.base import BaseCommand, CommandError
from video.models import LocalSource as LocalSource
from video.models import Source as Source
from video.models import Sink as Sink
from detect.models import Recognizer as Recognizer
from detect.models import Face as Face
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
gohome = False



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
        raw_name = sink.short_id
        sink = src.overlay_sink
        overlay_name = sink.short_id
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
                if len(faces) > 1:
                    model.train(images, lables)


                os.close(r)
                os.close(r1)
                os.close(sys.stdout.fileno())
                os.close(sys.stderr.fileno())
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

                while not gohome:
                    ret, frame = video_capture.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    mini = cv2.resize(gray, (gray.shape[1] / size, gray.shape[0] / size))
                    cv2.rectangle(frame, (0, 0), (640, 20), (0, 0, 0), -1)
                    cv2.putText(frame, name + " " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), (5, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (255, 255, 255))

                    sys.stdout.write(frame.tostring())
                    if motion_detection:
                        fgmask = fgbg.apply(gray)
                        fgmask = cv2.blur(fgmask, (10, 10))

                    framenr += 1
                    if (framenr)==3:
                        framenr = 0

                        # Movement detection
                        if motion_detection:
                            fgbg = cv2.BackgroundSubtractorMOG2(history=3,varThreshold=motion_threshold,bShadowDetection=True)
                            fgbg.setDouble("fVarInit",100)
                            fgbg.setDouble("fVarMin",100)
                            fgbg.setDouble("fCT",0.1)
                            fgbg.setDouble("fTau",0.5)
                            delta_count = cv2.countNonZero(fgmask)
                            if (delta_count!=0):
                                cv2.putText(frame, "MOVEMENT", (565, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (20, 20, 255))
                                contours, hierarchy = cv2.findContours(fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
                                cv2.drawContours(frame, contours, -1, (0,0,255), 1)

                        # Recognition
                        if recognizer:
                            faces = faceCascade.detectMultiScale(
                                mini,
                                scaleFactor=1.1,
                                minNeighbors=5,
                                flags=0,
                                minSize=(15, 15),
                            )

                            for i in range(len(faces)):
                                face_i = faces[i]
                                (x, y, w, h) = [v * size for v in face_i]
                                face = gray[y:y + h, x:x + w]
                                face_resize = cv2.resize(face, (im_width, im_height))
                                prediction = model.predict(face_resize)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                if names.has_key(prediction[0]):
                                    cv2.putText(frame,
                                        '%s' % (names[prediction[0]]),
                                        (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1.2,(0, 255, 0))
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
