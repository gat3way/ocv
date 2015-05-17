from django.db import models
import sentinel.settings.common as settings
import os
from detect.models import FaceRecognizer as FaceRecognizer
from detect.models import SmokeRecognizer as SmokeRecognizer


# Create your models here.


def get_stream_url(url,username,password):
    if not "@" in url and (len(username)>0 or len(password)>0):
        videourls = url.split("http://")
        if len(videourls)==1:
            videourls = url.split("https://")
            if len(videourls)==1:
                videourls = url.split("rtsp://")
                if len(videourls)==1:
                    raise Exception("Malformed URL")
                else:
                    proto="rtsp://"
            else:
                proto = "https://"
        else:
            proto = "http://"
        address = videourls[1]
        newvideourl = proto + username + ":" + password + "@" +address
        return newvideourl

    if "@" in url and (len(username)>0 or len(password)>0):
        videourls = url.split("http://")
        if len(videourls)==1:
            videourls = url.split("https://")
            if len(videourls)==1:
                videourls = url.split("rtsp://")
                if len(videourls)==1:
                    raise Exception("Malformed URL")
                else:
                    proto="rtsp://"
            else:
                proto = "https://"
        else:
            proto = "http://"
        address = videourls[1]
        adresses = address.split("@")
        if len(addresses)==1:
            raise Exception("Malformed URL")
        address = addresses[1]

        newvideourl = proto + username + ":" + password + "@" +address
        return newvideourl



class Sink(models.Model):
    name = models.CharField(max_length=200)
    short_id = models.CharField(max_length=200, unique=True, default=None)

    def __str__(self):
        return self.name


class Storage(models.Model):
    BACKENDS = (
        ('local', 'Local filesystem'),
        ('http', 'HTTP upload'),
        ('ftp', 'FTP upload'),
    )
    name = models.CharField(max_length=200)
    backend = models.CharField(max_length=10, choices=BACKENDS)
    url = models.CharField(max_length=200)
    username = models.CharField(max_length=200, blank=True)
    password = models.CharField(max_length=200, blank=True)
    remote_dir = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return self.name

class LocalSource(models.Model):
    COLORSPACE = (
        ('gray', 'Grayscale'),
        ('8bit', '8 bit'),
        ('24bit', '24 bit'),
    )

    CONTROL = (
        ('none', 'None'),
        ('post', 'HTTP POST'),
        ('get', 'HTTP GET'),
        ('local', 'Local (IOCTL)'),
    )

    MOTION_TYPE = (
        ('rel', 'Relative'),
        ('abs', 'Absolute'),
    )



    name = models.CharField(max_length=200)
    height = models.IntegerField(default=480,blank=True)
    width = models.IntegerField(default=640,blank=True)
    fps = models.IntegerField(default=20,blank=True)

    url = models.CharField(max_length=200) 
    videourl = models.CharField(max_length=200, blank=True, null=True, default="")
    audiourl = models.CharField(max_length=200, blank=True, null=True, default="")

    username = models.CharField(max_length=32, blank=True, null=True, default="")
    password = models.CharField(max_length=32, blank=True, null=True, default="")
    requireadmincredentials = models.BooleanField(default=False)
    audiodata = models.CharField(max_length=200, blank=True, null=True, default="")
    color = models.CharField(max_length=10, choices=COLORSPACE, blank=True, null=True, default="24bit")
    zoomurl = models.CharField(max_length=200, blank=True, null=True, default="")
    zoomcontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    zoomtype = models.CharField(max_length=10, choices=MOTION_TYPE, blank=True, null=True, default="none")
    zoomdata = models.CharField(max_length=200, blank=True, null=True, default="")
    zoommin = models.IntegerField(default=0,blank=True)
    zoommax = models.IntegerField(default=0,blank=True)

    ptz_type = models.CharField(max_length=10, choices=MOTION_TYPE, blank=True, null=True, default="none")
    ptz_control = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    ptz_step_min = models.IntegerField(default=0,blank=True)
    ptz_step_max = models.IntegerField(default=0,blank=True)
    ptz_min = models.IntegerField(default=0,blank=True)
    ptz_max = models.IntegerField(default=0,blank=True)

    ptz_up = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_up_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_up_right = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_up_right_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_right = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_right_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom_right = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom_right_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom_left = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_bottom_left_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_left = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_left_data = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_up_left = models.CharField(max_length=200, blank=True, null=True, default="")
    ptz_up_left_data = models.CharField(max_length=200, blank=True, null=True, default="")

    reseturl = models.CharField(max_length=200, blank=True, null=True, default="")
    resetcontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    resetdata = models.CharField(max_length=200, blank=True, null=True, default="")

    nightmodeurl = models.CharField(max_length=200, blank=True, null=True, default="")
    nightmodecontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    nightmodedata = models.CharField(max_length=200, blank=True, null=True, default="")
    daymodeurl = models.CharField(max_length=200, blank=True, null=True, default="")
    daymodecontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    daymodedata = models.CharField(max_length=200, blank=True, null=True, default="")
    automodeurl = models.CharField(max_length=200, blank=True, null=True, default="")
    automodecontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    automodedata = models.CharField(max_length=200, blank=True, null=True, default="")
    profileurl = models.CharField(max_length=200, blank=True, null=True, default="")
    profiledata = models.CharField(max_length=200, blank=True, null=True, default="")
    profilecontrol = models.CharField(max_length=10, choices=CONTROL, blank=True, null=True, default="none")
    profilemin = models.IntegerField(default=0,blank=True)
    profilemax = models.IntegerField(default=0,blank=True)
    is_setup = models.BooleanField(default=False,blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not "@" in self.videourl and (len(self.username)>0 or len(self.password)>0):
            self.videourl = get_stream_url(self.videourl,self.username,self.password)
            self.audiourl = get_stream_url(self.audiourl,self.username,self.password)


        super(LocalSource,self).save(*args, **kwargs)
        command = os.path.join(settings.PROJECT_ROOT,"manage.py")
        os.system(command + " daemon stop")




class Source(models.Model):
    url = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    device = models.ForeignKey(LocalSource, related_name="device", blank=True, null=True)
    raw_sink = models.ForeignKey(Sink, related_name="raw")
    overlay_sink = models.ForeignKey(Sink, related_name="overlay", blank=True, null=True)
    storage = models.ForeignKey(Storage, related_name="storage")
    store_archive = models.BooleanField(default=True)
    top_blank_pixels = models.IntegerField(default=0)
    bottom_blank_pixels = models.IntegerField(default=0)
    left_blank_pixels = models.IntegerField(default=0)
    right_blank_pixels = models.IntegerField(default=0)


    tamper_detection = models.BooleanField(default=True)
    motion_detection = models.BooleanField(default=True)
    motion_threshold = models.IntegerField(default=15)
    motion_exclude = models.CharField(max_length=1024, editable=False, default="", blank=True, null=True)
    face_recognizer = models.ForeignKey(FaceRecognizer, related_name="face_recognizer", blank=True, null=True)
    smoke_detector = models.ForeignKey(SmokeRecognizer, related_name="smoke_recognizer", blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        #if self.device:
        #    device = LocalSource.objects.get(name=self.device)
        #    self.url = device.url
        super(Source,self).save(*args, **kwargs)
        command = os.path.join(settings.PROJECT_ROOT,"manage.py")
        os.system(command + " daemon stop")
