#!/usr/bin/env python
import cv2
from cv2 import cv
import sentinel.settings.common as settings
import numpy as np
from scipy import ndimage
import os

class FaceRecognizer(object):

    def __init__(self, faces, threshold=2000000000):
        self.size = 1
        (images, images2, self.labels, self.names, id) = ([], [], [], {}, 0)
        self.faces = faces

        # Load user face models
        fn_dir = os.path.join(settings.PROJECT_ROOT,"run","models")
        for face in self.faces:
            if face.active:
                self.names[id] = face.name
                subjectpath = os.path.join(fn_dir, face.name)
                for filename in os.listdir(subjectpath):
                    path = subjectpath + '/' + filename
                    label = id
                    #images.append(cv2.imread(path, 0))
                    images.append(self.tantriggs(cv2.imread(path, 0)))
                    self.labels.append(int(label))
                id += 1

        # Load default models
        fn_dir = os.path.join(settings.PROJECT_ROOT,"run","att_models")
        for (subdirs, dirs, files) in os.walk(fn_dir):
            for subdir in dirs:
                self.names[id] = ''
                subjectpath = os.path.join(fn_dir, subdir)
                for filename in os.listdir(subjectpath):
                    path = subjectpath + '/' + filename
                    label = id
                    #images.append(cv2.imread(path, 0))
                    images.append(self.tantriggs(cv2.imread(path, 0)))
                    self.labels.append(int(label))
                id += 1

        # Prepare recognizer
        (self.im_width, self.im_height) = (112, 92)
        (self.images, self.labels) = [np.array(lis) for lis in [images, self.labels]]
        self.model = cv2.createFisherFaceRecognizer()
        self.model.setDouble("threshold",threshold)
        self.model2 = cv2.createLBPHFaceRecognizer()
        self.model2.setDouble("threshold",threshold)
        if id > 1:
            self.model.train(self.images, self.labels)
            self.model2.train(self.images, self.labels)


        # Prepare face cascade
        self.faceCascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(os.path.realpath(__file__)),"haarcascade_frontalface_default.xml"))
        self.framenr = 0


    # TanTriggs transform
    def tantriggs(self, x, alpha=0.1,gamma=0.2,sigma0=1,sigma1=2,tau=10.0):
        x = np.array(x, dtype=np.float32)
        x = np.power(x, gamma)
        s0 = 3*sigma0
        s1 = 3*sigma1
        if ((s0%2)==0):
            s0+=1
        if ((s1%2)==0):
            s1+=1

        x = np.asarray(
            ndimage.gaussian_filter(x, sigma0) - ndimage.gaussian_filter(x, sigma1)
            )

        x = x / np.power(
            np.mean(np.power(np.abs(x), alpha)),
            1.0 / alpha
            )
        x = x / np.power(
                np.mean(
                    np.power(
                        np.minimum(np.abs(x), tau),
                        alpha
                    )
                ),
                1.0 / alpha
            )

        x = np.tanh(x / tau) * tau
        x = cv2.normalize(x,x,-220,0,cv2.NORM_MINMAX)
        return np.array(x, np.uint8)




    def capture(self, frame):
        self.gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frame_orig = self.gray.copy()
        self.gray = cv2.resize(self.gray, (int(frame.shape[1] / 2), int(frame.shape[0] / 2)))


    def analyze(self, frame):
        frame2 = frame.copy()
        mini = self.gray
        faces = self.faceCascade.detectMultiScale(
                        mini,
                        scaleFactor=1.5,
                        minNeighbors=10,
                        flags=0,
                        minSize=(5, 5),
                    )

        detected_faces = []
        for i in range(len(faces)):
            print "FACE!"
            size = 2
            face_i = faces[i]
            (x, y, w, h) = [int(v * size) for v in face_i]
            face = self.frame_orig[y:y + h, x:x + w]
            face_resize = cv2.resize(face, (self.im_width, self.im_height))
            face_resize2 = self.tantriggs(face_resize)
            prediction = self.model.predict(face_resize2)
            if self.names.has_key(prediction[0]):
                prediction2 = self.model2.predict(face_resize2)
                if self.names.has_key(prediction2[0]) and prediction2[0]==prediction[0]:
                    cv2.rectangle(frame2, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame2, '%s' % (self.names[prediction[0]]), (x-10, y-10), cv2.FONT_HERSHEY_PLAIN,1.2,(0, 255, 0))
                    # Log face!
                    detected_faces.append(self.names[prediction[0]])
                else:
                    cv2.rectangle(frame2, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    detected_faces.append("")
            else:
                cv2.rectangle(frame2, (x, y), (x + w, y + h), (0, 255, 0), 2)
                detected_faces.append("")


        return detected_faces, frame2

