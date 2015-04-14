from django.db import models
from django.forms import forms
from video.models import Storage as Storage
import cv2
import cv2.cv
import os
import sentinel.settings.common as settings

# Create your models here.


class ContentTypeRestrictedFileField(models.FileField):
    def __init__(self, *args, **kwargs):
        try:
            self.content_types = kwargs.pop("content_types")
            self.max_upload_size = kwargs.pop("max_upload_size")
            self.model_name = kwargs.pop("model_name")
        except Exception:
            pass
        super(ContentTypeRestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):        
        data = super(ContentTypeRestrictedFileField, self).clean(*args, **kwargs)

        try:
            content_type = file.content_type
            if content_type in self.content_types:
                if file._size > self.max_upload_size:
                    raise forms.ValidationError('Please keep filesize under %s. Current filesize %s' % (filesizeformat(self.max_upload_size), filesizeformat(file._size)))
            else:
                raise forms.ValidationError('Filetype not supported.')
        except AttributeError:
            pass

        return data


class Recognizer(models.Model):
    TYPES = (
        ('facial', 'Facial Recognition'),
    )
    name = models.CharField(max_length=200)
    rtype = models.CharField(max_length=20, choices=TYPES)
    def __str__(self):
        return self.name


class Face(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField()
    recognizer = models.ForeignKey(Recognizer, related_name="f_recognizer")
    training_video = ContentTypeRestrictedFileField(
            content_types=['video/x-msvideo', 'video/mp4', 'video/x-flv', 'video/mpeg'],
            model_name = name,
            max_upload_size=5242880, default='')

    def __str__(self):
        return self.name

    def clean(self, *args, **kwargs):

        content_types=['video/x-msvideo', 'video/mp4', 'video/x-flv', 'video/mpeg']

        # Training video not uploaded this time
        if not hasattr(self.training_video.file,"content_type"):
            upload = False
        else:
            upload = True

        if upload:
            if self.training_video.file.content_type not in content_types:
                raise forms.ValidationError('Not a recognized video file format')

        if upload:
            fn_dir = os.path.join(settings.PROJECT_ROOT,"run","models")
            fn_haar = os.path.join(settings.PROJECT_ROOT,"sentinel","management","commands","haarcascade_frontalface_default.xml")
            fn_name = self.name
            vid_name = self.training_video.path
            self.training_video.open()
            data = self.training_video.read()
            fn = open(vid_name,"w")
            fn.write(data)
            fn.close()

            size = 4
            path = os.path.join(fn_dir, fn_name)

            if not os.path.isdir(path):
                os.mkdir(path)

            # First, clean previous images if any
            filelist = [ f for f in os.listdir(path) if f.endswith(".png") ]
            for f in filelist:
                os.remove(os.path.join(path,f))

            (im_width, im_height) = (112, 92)
            haar_cascade = cv2.CascadeClassifier(fn_haar)
            try:
                webcam = cv2.VideoCapture(vid_name)
            except Exception:
                os.remove(vid_name)
                filelist = [ f for f in os.listdir(path) if f.endswith(".png") ]
                for f in filelist:
                    os.remove(os.path.join(path,f))
                raise forms.ValidationError('Could not read video')

            count = 0
            while count < 30:
                try:
                    (rval, im) = webcam.read()
                except Exception:
                    filelist = [ f for f in os.listdir(path) if f.endswith(".png") ]
                    for f in filelist:
                        os.remove(os.path.join(path,f))
                    os.remove(vid_name)
                    raise forms.ValidationError('Not enough face frames detected on video')

                im = cv2.flip(im, 1, 0)
                try:
                    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                except Exception:
                    filelist = [ f for f in os.listdir(path) if f.endswith(".png") ]
                    for f in filelist:
                        os.remove(os.path.join(path,f))
                    os.remove(vid_name)
                    raise forms.ValidationError('Could not read video or not enough faces')
                mini = cv2.resize(gray, (gray.shape[1] / size, gray.shape[0] / size))
                faces = haar_cascade.detectMultiScale(mini)
                faces = sorted(faces, key=lambda x: x[3])
                if faces:
                    face_i = faces[0]
                    (x, y, w, h) = [v * size for v in face_i]
                    face = gray[y:y + h, x:x + w]
                    face_resize = cv2.resize(face, (im_width, im_height))
                    pin=sorted([int(n[:n.find('.')]) for n in os.listdir(path) if n[0]!='.' ]+[0])[-1] + 1
                    cv2.imwrite('%s/%s.png' % (path, pin), face_resize)
                    count += 1

            os.remove(vid_name)


        # Check if name is changed - so that we rename directory as needed
        old_instance = Face.objects.get(pk=self.pk)
        if old_instance.name != self.name:
            fn_dir = os.path.join(settings.PROJECT_ROOT,"run","models")
            fn_name = self.name
            path = os.path.join(fn_dir, fn_name)
            path_old = os.path.join(fn_dir, old_instance.name)
            os.renames(path_old, path)


        super(Face, self).clean(*args, **kwargs)
        command = os.path.join(settings.PROJECT_ROOT,"manage.py")
        os.system(command + " daemon stop")

        #super(Face, self).save(*args, **kwargs)