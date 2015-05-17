#!/usr/bin/env python
import cv2
from cv2 import cv



class TamperDetector(object):

    def __init__(self, tamper_threshold=10):
        self.tamper_entropy_old = self.tamper_entropy_mid = self.tamper_entropy_now = None
        self.fn = 0
        self.tamper = False



    def capture(self, frame):
        self.fn += 1

        if (self.fn%60==0):
            r1 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist_img = cv2.calcHist([r1],[0],None,[256],[0,256])
            hist_img /= (640*480)
            lhist = cv2.log(hist_img)
            hist_img = (lhist*hist_img)
            if self.tamper_entropy_mid:
                self.tamper_entropy_old = self.tamper_entropy_mid
            if self.tamper_entropy_now:
                self.tamper_entropy_mid = self.tamper_entropy_now
            self.tamper_entropy_now = -(hist_img.sum())

            if self.tamper_entropy_now and self.tamper_entropy_mid and self.tamper_entropy_old:
                if abs(self.tamper_entropy_now - self.tamper_entropy_mid) > min(self.tamper_entropy_now, self.tamper_entropy_mid) / 10 \
                and abs(self.tamper_entropy_now - self.tamper_entropy_old) > min(self.tamper_entropy_now,self.tamper_entropy_old) / 10:
                    self.tamper = True
                else:
                    self.tamper = False



    def analyze(self, frame):
        return self.tamper,frame

