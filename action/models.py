from django.db import models
from video.models import Source
from detect.models import Face
from .signals import event_logged
from sentinel.settings import common as settings
from django.utils import timezone
import datetime

# Create your models here.



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
    user = models.ForeignKey(
        getattr(settings, "AUTH_USER_MODEL", "auth.User"),
        null=True,
        on_delete=models.SET_NULL
    )
    comment = models.CharField(max_length=200, null=True, blank=True)
    extra = models.CharField(max_length=200, null=True, blank=True)

    #def save:
    #    super(Event,self).save(*args, **kwargs)

    def get_url(self):
        return '<a href="/static/snapshots/{}" target="_blank">Snapshot</a>'.format(self.image)


    class Meta:
        ordering = ["-timestamp"]


def log(user, name, e_type, image=None, face=None, source=None, comment=None, extra=None, time_offset=0):
    if (user is not None and not user.is_authenticated()):
        user = None
    if extra is None:
        extra = {}
    event = Event.objects.create(user=user, name=name,e_type=e_type,image=image,face=face,source=source,comment=comment, extra=extra, timestamp = datetime.datetime.now() + datetime.timedelta(0,time_offset))
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

