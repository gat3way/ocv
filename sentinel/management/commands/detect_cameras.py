from django.core.management.base import BaseCommand, CommandError
from video.models import LocalSource as LocalSource
import cv2
from cv2 import cv
import sys
import backend.discovery.upnp as upnp

class Command(BaseCommand):
    help = 'Detect available cameras connected to the system'

    def handle(self, *args, **options):
        self.stdout.write('Detecting cameras...\n')
        done = False
        nr = 0
        sys.stderr.close()
        while not done:
            try:
                capture = cv2.VideoCapture(nr)
            except Exception:
                self.stdout.write("PROBLEM!")
                done = True
            if not done:
                try:
                    height = int(capture.get(cv.CV_CAP_PROP_FRAME_WIDTH))
                    width = int(capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
                except Exception:
                    height = width = 0
                    done = True
                    continue

                if height == 0:
                    done = True
                    continue
                try:
                    fps = int(capture.get(cv.CV_CAP_PROP_FPS))
                except Exception:
                    fps = 0

                url = str(nr)
                name = "Camera " + str(nr) + ' ('+ str(width)+'x'+str(height)+' @ '+str(fps)+' fps)'
                dev,created = LocalSource.objects.get_or_create(name=name,fps=fps,url=url,height=height,width=width)
                nr += 1
                self.stdout.write('Detected device ' + name + '('+ str(width)+'x'+str(height)+' @ '+str(fps)+' fps)\n')


        # Detect UPnP stuff
        locations = upnp.discovery()
        devices = upnp.get_devices(locations)
        for dev in devices:
            matched = upnp.match(dev)
            if matched:
                print matched["friendlyname"], matched["videourl"]
                upnp.create_device(matched)
