from django.core.management.base import BaseCommand, CommandError
import sentinel.settings.common as settings
from video.models import Sink as Sink
from video.models import LocalSource as LocalSource
from video.models import Source as Source
from backend.ivs.motiondetection import MotionDetector
import cv2
from cv2 import cv
import sys
import Image
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO
import time
import mmap
import os
import numpy as np
import urlparse
import threading
import random
import hashlib
import signal
import urllib2


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class CamHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        req = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(req.query)
        document = req.path
        aspect = 2
        if params.has_key("aspect"):
            aspect = int(params["aspect"][0])
        resx = 320*aspect
        resy = 240*aspect


        if '.mjpg' in document:

            if params.has_key("snapshot"):
                filename = os.path.join(settings.PROJECT_ROOT,"run","snapshots",params["snapshot"][0])
                if not os.path.isfile(filename):
                    return
                dev = cv2.VideoCapture(filename)
            else:
                short_id = document[1:].split(".mjpg")[0]
                short_id = urllib2.unquote(short_id).decode('utf8')
                #short_id = document[1:].split(".")[0]
                try:
                    sink = Sink.objects.get(name=short_id)
                    short_id = sink.short_id
                except Exception:
                    import traceback
                    traceback.print_exc()
                    return
                if not sink:
                    return

                filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",short_id)
                if not os.path.isfile(filename):
                    return
                size = os.path.getsize(filename)
                f = open(filename, 'r')
                m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                capture = m

            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            fn = 0
            hashed = ""
            nosignal = False

            while True:

                try:
                    if params.has_key("snapshot"):
                        res,img = dev.read()
                    else:
                        capture.seek(0, os.SEEK_SET)
                        dt = np.dtype((np.uint8, 3))
                        img = np.fromstring(capture.read(size), dt)
                        if size==640*480*3:
                            img = np.reshape(img,(480,640,3))
                        elif size==320*240*3:
                            img = np.reshape(img,(240,320,3))
                        elif size==960*720*3:
                            img = np.reshape(img,(720,960,3))
                        elif size==1280*960*3:
                            img = np.reshape(img,(960,1280,3))
                        else:
                            print "UNKNOWN SIZE:"+str(size)
                        img = cv2.resize(img, (resx,resy))

                    r,buf=cv2.imencode(".jpg",img)
                    JpegData=buf.tostring()

                    if (fn%30)==0:
                        hasher = hashlib.md5()
                        hasher.update(JpegData)
                        hashed_new = hasher.hexdigest()
                        if hashed_new==hashed:
                            nosignal = True
                        else:
                            nosignal = False
                        hashed = hashed_new
                    fn += 1

                    if nosignal:
                        empty = np.zeros((img.shape[0],img.shape[1],3), np.uint8)
                        cv2.putText(empty,'No Signal', (int((260*img.shape[0])/480), int((230*img.shape[1])/640)), cv2.FONT_HERSHEY_PLAIN,1.5*((resx+0.1)/640),(255, 255, 255))
                        r,buf=cv2.imencode(".jpg",empty)
                        JpegData=buf.tostring()


                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(len(JpegData)))
                    self.end_headers()
                    self.wfile.write(JpegData)
                    time.sleep(0.05)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    return
            return


        if '.vidtest' in document:
            req = urlparse.urlparse(self.path)
            params = urlparse.parse_qs(req.query)
            document = req.path
            short_id = document[1:].split(".vidtest")[0]
            short_id = urllib2.unquote(short_id).decode('utf8')
            motiondetector = None
            if params.has_key("motion_test") and params.has_key("motion_threshold") and params.has_key("motion_exclude"):
                motionexclude = urllib2.unquote(params["motion_exclude"][0]).decode('utf8')
                motiondetector = MotionDetector(float(params["motion_threshold"][0]), motionexclude)

            sink = None
            try:
                localsource = LocalSource.objects.get(name=short_id)
                source = Source.objects.get(device = localsource)
                sink = source.raw_sink
            except Exception:
                print short_id
                import traceback
                traceback.print_exc()
                return


            if sink:
                filename = os.path.join(settings.PROJECT_ROOT,"run","sinks",sink.short_id)
                if not os.path.isfile(filename):
                    print "NOTFILE?"
                    return
                size = os.path.getsize(filename)
                f = open(filename, 'r')
                m = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                capture = m
            else:
                capture = cv2.VideoCapture(localsource.videourl)


            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.end_headers()
            fn = 0
            hashed = ""
            nosignal = False


            while True:
                try:
                    if sink:
                        capture.seek(0, os.SEEK_SET)
                        dt = np.dtype((np.uint8, 3))
                        img = np.fromstring(capture.read(size), dt)
                        if size==640*480:
                            img = np.reshape(img,(480,640,3))
                        elif size==320*240:
                            img = np.reshape(img,(240,320,3))
                        elif size==960*720:
                            img = np.reshape(img,(720,960,3))
                        elif size==1280*960:
                            img = np.reshape(img,(960,1280,3))
                        img = cv2.resize(img, (resx,resy))
                    else:
                        res,img = capture.read()
                        if not res:
                            return
                        img = cv2.resize(img, (resx,resy))

                    cv2.rectangle(img, (0, 0), (resx, 20), (0, 0, 0), -1)


                    if motiondetector:
                        motiondetector.capture(img)
                        movement,img = motiondetector.analyze(img)


                    r,buf=cv2.imencode(".jpg",img)
                    JpegData=buf.tostring()


                    if (fn%30)==0:
                        hasher = hashlib.md5()
                        hasher.update(JpegData)
                        hashed_new = hasher.hexdigest()
                        if hashed_new==hashed:
                            nosignal = True
                        else:
                            nosignal = False
                        hashed = hashed_new
                    fn += 1

                    if nosignal:
                        empty = np.zeros((img.shape[0],img.shape[1],3), np.uint8)
                        cv2.putText(empty,'No Signal', (int((260*img.shape[0])/480), int((230*img.shape[1])/640)), cv2.FONT_HERSHEY_PLAIN,1.5*((resx+0.1)/640),(255, 255, 255))
                        r,buf=cv2.imencode(".jpg",empty)
                        JpegData=buf.tostring()


                    self.wfile.write("--jpgboundary")
                    self.send_header('Content-type','image/jpeg')
                    self.send_header('Content-length',str(len(JpegData)))
                    self.end_headers()
                    self.wfile.write(JpegData)
                    time.sleep(0.05)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    return
            return






        if '.html' in document:
            req = urlparse.urlparse(self.path)
            params = urlparse.parse_qs(req.query)
            document = req.path
            short_id = document[1:].split(".")[0]
            if params.has_key("snapshot"):
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('<img src="http://127.0.0.1:8090/snapshot.mjpg?snapshot='+params["snapshot"][0]+'aspect='+aspect+'&token='+str(random.random())+'"/>')
                self.wfile.write('</body></html>')
            else:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('<img src="http://127.0.0.1:8090/' + short_id +'.mjpg?token='+str(random.random())+'aspect='+aspect+'&motion_test=1&motion_threshold=30&motion_exclude=[]"/>')
                self.wfile.write('</body></html>')
            return


# Signal handler for SIGBUS (which would occasionally get thrown while trying to read the mmaped file)
def sigbus_handler(signum, frame):
    print "SIGBUS"



class Command(BaseCommand):
    help = 'Stream mjpeg'


    def handle(self, *args, **options):
        signal.signal(signal.SIGBUS, sigbus_handler)

        try:
            server = ThreadedHTTPServer(('',8090),CamHandler)
            print "server started"
            server.serve_forever()
        except KeyboardInterrupt:
            server.socket.close()
