#!/usr/bin/env python
import cv2
from cv2 import cv
import numpy as np
import json



class MotionDetector(object):

    def __init__(self,motion_threshold, motion_exclude):
        self.motion_threshold = motion_threshold*5
        if self.motion_threshold < 0:
            self.motion_threshold = 1
        self.fgbg = cv2.BackgroundSubtractorMOG2(history=3,varThreshold=self.motion_threshold,bShadowDetection=True)
        try:
            self.regions = json.loads(motion_exclude)
        except Exception:
            import traceback
            traceback.print_exc()
            self.regions = { 'rects' : [] }
        self.first = True

    def capture(self, gray):
        gray2 = cv2.resize(gray, (int(gray.shape[1] / 2), int(gray.shape[0] / 2)))
        gray2 = cv2.cvtColor(gray2,cv2.COLOR_BGR2GRAY)
        if self.first:
            self.fgmask = gray2
            self.first = False
        for rect in self.regions["rects"]:
            x1 = rect["x"]
            y1 = rect["y"]
            x2 = rect["w"]+x1
            y2 = rect["h"]+y1
            cv2.rectangle(gray2, (x1/2, y1/2), (x2/2, y2/2), (0, 0, 0), -1)
        self.fgmask = self.fgbg.apply(gray2,self.fgmask,0.1)
        self.fgmask = cv2.blur(self.fgmask, (10, 10))


    def analyze(self, frame):
        delta_count = cv2.countNonZero(self.fgmask)
        frame2 = frame.copy()
        if (delta_count!=0):
            frame2 = frame.copy()
            movement = True
            cv2.putText(frame2, "MOVEMENT", (565, 15), cv2.FONT_HERSHEY_PLAIN, 0.8, (20, 20, 255))
            self.fgmask = cv2.resize(self.fgmask, (int(self.fgmask.shape[1] * 2), int(self.fgmask.shape[0] * 2)))
            contours, hierarchy = cv2.findContours(self.fgmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame2, contours, -1, (0,0,255), 1)
        else:
            movement = False

        return movement, frame2


