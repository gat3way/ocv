from django.db import models
from video.models import Source
from detect.models import Face
from .signals import event_logged
from sentinel.settings import common as settings
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
import datetime
import random
import os



class Event(models.Model):

    E_TYPES = (
        ('trigger', 'Trigger'),
        ('alert', 'Alert'),
        )
    e_type = models.CharField(max_length=10, choices=E_TYPES, blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    timestamp = models.DateTimeField(default=datetime.datetime.now(), db_index=True)
    face = models.ForeignKey(Face,related_name="face", blank=True, null=True)
    source = models.ForeignKey(Source, related_name="source", blank=True, null=True)
    image = models.CharField(max_length=64, blank=True, null=True)
    video = models.CharField(max_length=64, blank=True, null=True)
    user = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    comment = models.CharField(max_length=200, null=True, blank=True)
    extra = models.CharField(max_length=200, null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    #def save:
    #    super(Event,self).save(*args, **kwargs)

    def get_s_url(self):
        return '<a href="/static/snapshots/{}" target="_blank">Snapshot</a>'.format(self.image)
    def get_v_url(self):
        html = '<a href="http://localhost:8090/snapshot.html?snapshot={0}&token={1}" target="_blank">Watch</a>'.format(self.video,random.random()*65535)
        html += '&nbsp;|&nbsp;'
        html += '<a href="/static/snapshots/{}" target="_blank">Download</a>'.format(self.video)
        return html

    def __str__(self):
        return self.name + " at " + self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    class Meta:
        ordering = ["-timestamp"]


def log(user, name, e_type, image=None, face=None, source=None, comment=None, extra=None, time_offset=0, video=None):
    if (user is not None and not user.is_authenticated()):
        user = None
    if extra is None:
        extra = ""
    event = Event.objects.create(user=user, name=name,e_type=e_type,image=image,face=face,source=source,comment=comment, extra=extra, timestamp = datetime.datetime.now() + datetime.timedelta(0,time_offset), video=video)
    event_logged.send(sender=Event, event=event)
    return event




class Alarm(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Action(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


@receiver(pre_delete, sender=Event)
def _event_delete(sender, instance, **kwargs):
    image = instance.image
    video = instance.video
    image_path = filename = os.path.join(settings.PROJECT_ROOT,"run","snapshots",image)
    if os.path.isfile(image_path):
        os.remove(image_path)
    video_path = filename = os.path.join(settings.PROJECT_ROOT,"run","snapshots",video)
    if os.path.isfile(video_path):
        os.remove(video_path)