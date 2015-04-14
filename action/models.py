from django.db import models

# Create your models here.



class Event(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Alarm(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Action(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

