from django.core.management.base import BaseCommand, CommandError
import sentinel.settings.common as settings
from video.models import Sink as Sink
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


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class CamHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        req = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(req.query)
        document = req.path

        if '.mjpg' in document:

            if params.has_key("snapshot"):
                filename = os.path.join(settings.PROJECT_ROOT,"run","snapshots",params["snapshot"][0])
                print filename
                if not os.path.isfile(filename):
                    return
                dev = cv2.VideoCapture(filename)
            else:
                short_id = document[1:].split(".")[0]
                try:
                    sink = Sink.objects.get(short_id=short_id)
                except Exception:
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
                        img = np.reshape(img,(480,640,3))

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
                        cv2.putText(empty,'No Signal', (int((260*img.shape[0])/480), int((230*img.shape[1])/640)), cv2.FONT_HERSHEY_PLAIN,1.5,(255, 255, 255))
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
                self.wfile.write('<img src="http://127.0.0.1:8090/snapshot.mjpg?snapshot='+params["snapshot"][0]+'&token='+str(random.random())+'"/>')
                self.wfile.write('</body></html>')
            else:
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('<img src="http://127.0.0.1:8090/' + short_id +'.mjpg?token='+str(random.random())+'"/>')
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
