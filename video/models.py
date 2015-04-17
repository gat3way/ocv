from django.db import models
import sentinel.settings.common as settings
import os

# Create your models here.



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
    url = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    height = models.IntegerField()
    width = models.IntegerField()
    fps = models.IntegerField()

    def __str__(self):
        return self.name



class Source(models.Model):
    url = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    device = models.ForeignKey(LocalSource, related_name="device", blank=True, null=True)
    raw_sink = models.ForeignKey(Sink, related_name="raw")
    overlay_sink = models.ForeignKey(Sink, related_name="overlay")
    storage = models.ForeignKey(Storage, related_name="storage")
    motion_detection = models.BooleanField(default=True)
    motion_threshold = models.IntegerField(default=15)
    from detect.models import Recognizer as Recognizer
    recognizer = models.ForeignKey(Recognizer, related_name="recognizer", blank=True, null=True)
    top_blank_pixels = models.IntegerField(default=0)
    bottom_blank_pixels = models.IntegerField(default=0)
    left_blank_pixels = models.IntegerField(default=0)
    right_blank_pixels = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.device:
            device = LocalSource.objects.get(name=self.device)
            self.url = device.url
        super(Source,self).save(*args, **kwargs)
        command = os.path.join(settings.PROJECT_ROOT,"manage.py")
        os.system(command + " daemon stop")
