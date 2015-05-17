#!/usr/bin/env python
import cv2
from cv2 import cv
import numpy as np


class SmokeDetector(object):

    def __init__(self, capture_dev, exposition, min_threshold, max_threshold):
        self.FRAMES = exposition
        self.FRAMES_BACK = 5
        self.MINCONTOUR = 100
        self.THRESHOLD_GEO = 20
        self.THRESHOLD_LOW = min_threshold
        self.THRESHOLD_HIGH = max_threshold
        self.THRESHOLD_RGB=10
        self.prevc = 0
        self.extents = []
        self.entropies = []
        self.points = []
        self.areas = []
        self.curs = []
        self.cx = []
        self.cy = []
        self.frames = []
        for a in range(0,self.FRAMES_BACK):
            var,s_fgmask = capture_dev.read()
            self.s_fgmask = cv2.resize(s_fgmask, (640, 480)) 
            self.frames.append(cv2.cvtColor(self.s_fgmask,cv2.COLOR_BGR2GRAY))
            self.empty_src = np.zeros((self.s_fgmask.shape[0], self.s_fgmask.shape[1],1), np.uint8)
            self.empty_srcmask = np.zeros((self.s_fgmask.shape[0], self.s_fgmask.shape[1],1), np.uint8)

            self.bground = self.frames.pop(0)
            self.bground2 = self.empty_src
            self.imagepixels = self.s_fgmask.shape[0]*self.s_fgmask.shape[1]
            self.fn = 0


    # Smoke detection RGB filters
    def rgbfilter_gray(self, image, rgbthreshold):
        b,g,r = cv2.split(image)
        rd = rgbthreshold
        min1 = cv2.min(b,g)
        min1 = cv2.min(min1,r)
        max1 = cv2.max(b,g)
        max1 = cv2.max(max1,r)

        diff = cv2.absdiff(max1,min1)
        res = cv2.compare(diff,rd,cv2.CMP_LT)
        return res


    def rgbfilter_black(self, image, image_bg):
        rd = 2
        rd2 = 100
        diff = cv2.subtract(image_bg,cv2.cvtColor(image,cv2.COLOR_BGR2GRAY))
        res = cv2.compare(diff,rd,cv2.CMP_GT)
        res1 = cv2.compare(diff,rd2,cv2.CMP_LT)
        return cv2.bitwise_and(res,res1)


    def rgbfilter_white(self, image,image_bg):
        rd = 2
        rd2 = 100
        diff = cv2.subtract(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),image_bg)
        res = cv2.compare(diff,rd,cv2.CMP_GT)
        res1 = cv2.compare(diff,rd2,cv2.CMP_LT)
        return cv2.bitwise_and(res,res1)


    def filters(self, image, image2, rgbthreshold):
        return cv2.threshold(cv2.bitwise_and(cv2.bitwise_or(self.rgbfilter_black(image,image2), self.rgbfilter_white(image,image2)), self.rgbfilter_gray(image,rgbthreshold)), 200, 255, cv2.THRESH_BINARY)




    def capture(self, frame):
        self.fn += 1
        if (self.fn % 60)==0:
            r,img2 = cv2.threshold(self.rgbfilter_gray(frame,self.THRESHOLD_RGB), self.THRESHOLD_RGB, 255, cv2.THRESH_BINARY)
            r = (cv2.countNonZero(img2)*100)/ (frame.shape[0]*frame.shape[1])
            if (r<20):
                if self.THRESHOLD_RGB<50:
                    self.THRESHOLD_RGB += 1
                elif (r>30):
                    if self.THRESHOLD_RGB>1:
                        self.THRESHOLD_RGB -= 1

        # Smoke detection processing here
        imgbg = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        imgbg = cv2.equalizeHist(imgbg)
        r,mask = self.filters(frame, self.bground, self.THRESHOLD_RGB)
        mask1 = cv2.bitwise_and(imgbg,mask)
        mask2 = cv2.bitwise_and(self.bground,mask)

        self.frames.append(imgbg)

        self.s_fgmask = cv2.absdiff(mask1,mask2)
        r,fgmask1 = cv2.threshold(self.s_fgmask, self.THRESHOLD_HIGH, 255, cv2.THRESH_BINARY_INV)
        r,fgmask2 = cv2.threshold(self.s_fgmask, self.THRESHOLD_LOW, 255, cv2.THRESH_BINARY)
        self.s_fgmask = cv2.bitwise_and(fgmask1,fgmask2)
        res = imgbg

        contours, hierarchy = cv2.findContours(self.s_fgmask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)

        self.contours2 = []
        extents_t = []
        entropies_t = []
        areas_t = []
        points_t = []
        cx_t = []
        cy_t = []

        extents_n = []
        entropies_n = []
        areas_n = []
        points_n = []
        quality_n = []
        self.index_n = []
        curs_n = []
        cx_n = []
        cy_n = []


        nowc = 0
        # Get data on our contours
        self.bground2 = self.bground

        for cnt in contours:
            area = cv2.contourArea(cnt)
            nowc+=area
            if area > self.MINCONTOUR:
                empty = self.empty_src.copy()
                cv2.drawContours(empty, cnt, -1, (255), -1)

                res1 = cv2.bitwise_and(self.bground2,empty)
                r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)

                hist_img = cv2.calcHist([res1],[0],msk,[256],[0,256])
                hist_img /= area
                bgmax = hist_img.max()
                lhist = cv2.log(hist_img)
                hist_img = (lhist*hist_img)
                entropy_bg = -(hist_img.sum())

                res1 = res
                res1 = cv2.bitwise_and(res1,empty)
                r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)

                hist = cv2.calcHist([res1],[0],msk,[256],[0,256])
                hist  /= area
                fgmax = hist.max()
                lhist = cv2.log(hist)
                hist = (lhist*hist)
                entropy_fg = -(hist.sum())

                res1 = cv2.absdiff(res,self.bground2)
                res1 = cv2.bitwise_and(res1,empty)
                r,msk = cv2.threshold(res1, 0, 255, cv2.THRESH_BINARY)


                hist2 = cv2.calcHist([res1],[0],msk,[256],[0,256])
                hist2  /= area
                fgmax = hist2.max()
                lhist = cv2.log(hist2)
                hist2 = (lhist*hist2)
                entropy_diff = -(hist2.sum())

                if (entropy_diff<entropy_fg and entropy_diff<entropy_bg):
                    self.contours2.append(cnt)
                    points_t.append(len(cnt))
                    (x,y,w,h) = cv2.boundingRect(cnt)

                    entropies_t.append((entropy_bg,entropy_fg,entropy_diff))
                    extents_t.append((x,y,w,h))
                    areas_t.append(area)
                    M = cv2.moments(cnt)
                    cx_t.append(int(M['m10']/M['m00']))
                    cy_t.append(int(M['m01']/M['m00']))


        if nowc>(((frame.shape[0]*frame.shape[1])*2)/3) and self.prevc!=0:
            for a in range(0,self.FRAMES_BACK):
                self.frames.pop(0)
                self.frames.append(mask1)
            extents_t = []
            entropies_t = []
            points_t = []
            areas_t = []
            curs_t = []
            cx_t = []
            cy_t = []
            self.extents = []
            self.entropies = []
            self.points = []
            self.areas = []
            self.curs = []
            self.cx = []
            self.cy = []
            self.prevc = nowc
        self.prevc = nowc

        for a in range(0,len(self.cx)):
            found = False
            for b in range(0,len(cx_t[:])):
                if not found and cx_t[b]>=0 and self.curs[a]>=0 and ((abs(self.cx[a]-cx_t[b])<self.THRESHOLD_GEO/2 \
                and abs(self.cy[a]-cy_t[b])<self.THRESHOLD_GEO/2) or (abs(self.cx[a]-cx_t[b])<self.THRESHOLD_GEO  \
                and abs(self.cy[a]-cy_t[b])<self.THRESHOLD_GEO)):
                    if ((self.areas[a]!=areas_t[b] or (extents_t[b]!=self.extents[a])) or self.points[a]!=points_t[b]) \
                    and abs(entropies_t[b][2]-self.entropies[a][2])<min(entropies_t[b][2],self.entropies[a][2]):
                        self.index_n.append(b)
                        extents_n.append(extents_t[b])
                        areas_n.append(areas_t[b])
                        points_n.append(points_t[b])
                        entropies_n.append(entropies_t[b])
                        cx_n.append(cx_t[b])
                        cy_n.append(cy_t[b])

                        #if curs[a]>=(FRAMES)/2:
                        #    print fn,entropies_t[b],entropies[a],curs[a]
                        curs_n.append(self.curs[a]+1)

                    extents_t[b] = -200
                    areas_t[b] = -200
                    points_t[b] = -200
                    cx_t[b] = -200
                    cy_t[b] = -200
                    found = True

        # Get new ones
        for a in range(0,len(extents_t)):
            if extents_t[a]>=0 and areas_t[a]>=0 and points_t[a]>0:
                curs_n.append(0)
                extents_n.append(extents_t[a])
                areas_n.append(areas_t[a])
                points_n.append(points_t[a])
                entropies_n.append((entropies_t[a][0],entropies_t[a][1],entropies_t[a][2]))
                self.index_n.append(a)
                cx_n.append(cx_t[a])
                cy_n.append(cy_t[a])

        # Copy over the new frames
        self.extents = extents_n[:]
        self.entropies = entropies_n[:]
        self.areas = areas_n[:]
        self.points = points_n[:]
        self.curs = curs_n[:]
        self.cx = cx_n[:]
        self.cy = cy_n[:]




    def analyze(self, frame):
        frame2 = frame.copy()
        r = 0
        result = False
        for a in range(0,len(self.curs)):
            if self.curs[a]>=self.FRAMES:
                cv2.drawContours(frame2, self.contours2, self.index_n[a], (0,0,255), -1)
                r += 1
        if r>0:
            result = True

        self.bground = self.frames.pop(0)

        return result, frame2
