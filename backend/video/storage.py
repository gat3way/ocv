#!/usr/bin/env python
import cv2
from cv2 import cv

import sentinel.settings.common as settings
from detect.models import Face as Face
import datetime
import backend.video.common as common
import sys
import os
import time
import numpy as np




class StorageManager(object):

    def __init__(self, queue, resolution=(640,480)):
        self.resolution = resolution
        self.queue = queue
        self.output = None

    def restart(self):
        r2,w2=os.pipe()
        self.queue.put(r2)
        self.queue.put(w2)
        self.output = os.fdopen(w2,"w")


    def write(self,frame):
        if self.output:
            data = frame.tostring()
            self.output.write(data)



    def switch_video(self,minute,pid,camname):
        # a hour expired, save new file
        minute2 = datetime.datetime.now().minute
        pid2 = pid

        if (minute2 != minute and minute2==0) or minute == -1:
            minute = minute2

            # Kill former process
            if pid2 != 0:
                os.kill(pid, signal.SIGTERM)
            rfd = wfd = None
            rfd = self.queue.get()
            wfd = self.queue.get()


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
                out = cv2.VideoWriter(path, fourcc, 20, self.resolution)
                sec = datetime.datetime.now().second
                fps = 0
                buffer = []
                while len(buffer)!=(self.resolution[0]*self.resolution[1])*3:
                    buffer = os.read(rfd,self.resolution[0]*self.resolution[1]*3)
                while datetime.datetime.now().second == sec:
                    time.sleep(0.01)
                sec = datetime.datetime.now().second
                dt = np.dtype((np.uint8, 3))
                while (datetime.datetime.now().second-sec)<3:
                    buffer = os.read(rfd,(self.resolution[0]*self.resolution[1])*3)
                    while len(buffer)!=(self.resolution[0]*self.resolution[1])*3:
                        buffer = os.read(rfd,(self.resolution[0]*self.resolution[1])*3)
                        if len(buffer)==0:
                            out.release()
                            return pid,minute2
                    img = np.fromstring(buffer, dt)
                    img = np.reshape(img,(self.resolution[1],self.resolution[0],3))
                    out.write(img)
                    time.sleep(0.03)
                    fps += 1
                fps /= 3
                fps = int(fps)
                sys.stderr.write("FPS = " + str(fps)+"\n")
                out.release()

                fourcc = cv2.cv.CV_FOURCC('F','M','P','4')
                out = cv2.VideoWriter(path, fourcc, fps, self.resolution)
                dt = np.dtype((np.uint8, 3))
                while True:
                    buffer = os.read(rfd,(self.resolution[0]*self.resolution[1])*3)
                    while len(buffer)!=(self.resolution[0]*self.resolution[1])*3:
                        buffer = os.read(rfd,(self.resolution[0]*self.resolution[1])*3)
                        if len(buffer)==0:
                            out.release()
                            return pid,minute2
                    img = np.fromstring(buffer, dt)
                    img = np.reshape(img,(self.resolution[1],self.resolution[0],3))
                    out.write(img)
                    time.sleep(0.03)
            else:
                os.close(rfd)
                os.waitpid(pid,os.WNOHANG)
                return pid3,minute2
        else:
            return pid,minute2

