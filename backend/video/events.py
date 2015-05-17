#!/usr/bin/env python
import cv2
from cv2 import cv

from detect.models import Face as Face
import datetime
import backend.video.common as common
from action.models import log as model_log


class EventHandler(object):

    def __init__(self):
        self.events = []


    def log(self, name, e_type, image=None, face=None, source=None, extra=None,frame=None,fps=0):
        r_face = None
        r_name = name
        if face and face!="":
            r_face = Face.objects.get(name=face)
            r_name = face + " Detected"

        entry = { "name" : r_name, "e_type" : e_type, "face": r_face, "source" : source, "extra" : extra}

        found = False
        found_event = None
        for event in self.events:
            if entry["name"] == event["name"] and entry["e_type"] == event["e_type"] and entry["face"] == event["face"] and entry["source"] == event["source"] and entry["extra"] == event["extra"]:
                found = True
                found_event = event
                break

        if not found:
            entry["image"] = common.save_picture(image)
            video,recorder = common.record_video(source,frame,fps)
            entry["video"] = video
            entry["recorder"] = recorder
            entry["timestamp"] = datetime.datetime.now()
            event = model_log(None, entry["name"], entry["e_type"], image=entry["image"], face=entry["face"], source=entry["source"], comment=None, extra=entry["extra"], time_offset=0, video=entry["video"])
            entry["event"] = event
            entry["toremove"] = False
            self.events.append(entry)
        else:
            found_event["timestamp"] = datetime.datetime.now()


    def update(self,frame):
        for event in self.events[:]:
            if event["recorder"]:
                common.write_video(event["recorder"], frame)
            if event["toremove"]:
                common.close_video(event["recorder"])
                self.events.remove(event)



    def cleanup(self):
        now = datetime.datetime.now()
        for event in self.events[:]:
            delta = now-event["timestamp"]
            if delta.total_seconds() > 5:
                event["event"].duration_seconds = (event["timestamp"]-event["event"].timestamp).total_seconds()
                event["event"].save()
                event["toremove"] = True


