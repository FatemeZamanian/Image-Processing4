# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import *
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QThread, Signal
from threading import Thread
import cv2


class Checkered(QThread):
    set_check_signal=Signal()

    def __init__(self):
        super(Checkered,self).__init__()
        self.video = cv2.VideoCapture(0)

    def run(self):
        face_detector = cv2.CascadeClassifier('fd.xml')
        while True:
            valid, frame = self.video.read()
            if valid is not True:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 3.1)

            for face in faces:
                x, y, w, h = face
                m=w//9
                n=h//9
                for i in range(x,x+w,m):
                    for j in range(y,y+h,n):
                        c=0
                        for xx in range(i,i+m):
                            for yy in range(j,j+n):
                                if xx>=480:
                                    xx=479
                                c+=gray[yy,xx]

                        c=c//(m*n)
                        gray[j:j+n,i:i+m]=c

            cv2.imwrite('f.jpg', gray)
            self.set_check_signal.emit()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


class Flip(QThread):
    set_flip_signal=Signal()
    def __init__(self):
        super(Flip,self).__init__()
        self.video = cv2.VideoCapture(0)
    def run(self):
        while True:
            valid, frame = self.video.read()
            if valid is not True:
                break
            frame = cv2.flip(frame, 0)
            cv2.imwrite('f.jpg', frame)
            self.set_flip_signal.emit()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break



class Mirror(QThread):
    set_mirror_signal=Signal()
    def __init__(self):
        super(Mirror,self).__init__()
        self.video = cv2.VideoCapture(0)
    def run(self):
        while True:
            valid, frame = self.video.read()
            if valid is not True:
                break
            (r, c, ch) = frame.shape
            left = frame[0:r, 0:c // 2]
            frame[0:r, c // 2:c] = cv2.flip(left, 1)
            cv2.imwrite('f.jpg', frame)
            self.set_mirror_signal.emit()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break



class Emoji(QThread):
    set_emoji_signal=Signal()
    def __init__(self):
        super(Emoji,self).__init__()
        self.emoji = cv2.imread('emoji.png',cv2.IMREAD_UNCHANGED)
        self.st_emoji=self.emoji[:,:,0:3]
        self.mask=self.emoji[:,:,3]
        self.st_emoji = cv2.cvtColor(self.st_emoji, cv2.COLOR_BGR2GRAY)
        self.video = cv2.VideoCapture(0)
    def run(self):
        face_detector = cv2.CascadeClassifier('fd.xml')
        while True:
            valid, frame = self.video.read()
            if valid is not True:
                break
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 3.5)
            for face in faces:
                x, y, w, h = face
                self.img_face=gray[y:y+h,x:x+w]
                self.st_emoji = cv2.resize(self.st_emoji, (w, h))
                self.mask = cv2.resize(self.mask, (w, h))
                self.st_emoji=self.st_emoji.astype(float)/255
                self.mask=self.mask.astype(float)/255
                self.img_face=self.img_face.astype(float)/255
                forg=cv2.multiply(self.mask,self.st_emoji)
                back=cv2.multiply(self.img_face,1-self.mask)
                res=cv2.add(back,forg)
                res *=255
                gray[y:y + h, x:x + w] = res
            cv2.imwrite('f.jpg',gray)
            self.set_emoji_signal.emit()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


class EyesMouth(QThread):

    set_em_signal=Signal()
    def __init__(self):
        super(EyesMouth,self).__init__()
        self.eyes = cv2.imread('eyes_emj.png')
        self.mouth=cv2.imread('lip.png')
        self.video = cv2.VideoCapture(0)
    def run(self):
        face_detector = cv2.CascadeClassifier('fd.xml')
        eye_detector = cv2.CascadeClassifier('parojosG.xml')
        lip_detector=cv2.CascadeClassifier('haarcascade_smile.xml')
        while True:
            valid, frame = self.video.read()
            if valid is not True:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 3.1)
            for face in faces:
                x, y, w, h = face
                eyes = eye_detector.detectMultiScale(gray[y:y + h, x:x + w],3.4)
                lips = lip_detector.detectMultiScale(gray[y:y + h, x:x + w],3.4)
                for lip in lips:
                    xl, yl, wl, hl = lip
                    self.mouth = cv2.resize(self.mouth, (wl, hl))
                    frame[y+yl:y+yl + hl, x+xl:x+xl + wl] = self.mouth

                for eye in eyes:
                    xe, ye, we, he = eye
                    self.eyes = cv2.resize(self.eyes, (we, he))
                    frame[y+ye:y+ye + he, x+xe:x+xe + we] = self.eyes
            cv2.imwrite('f.jpg',frame)
            self.set_em_signal.emit()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break




class camera(QWidget):
    def __init__(self):
        super(camera, self).__init__()
        loader = QUiLoader()
        self.ui = loader.load('form.ui')
        self.ui.show()
        self.ui.emoji_btn.clicked.connect(self.run_emoji)
        self.ui.el_btn.clicked.connect(self.run_le)
        self.ui.flip_btn.clicked.connect(self.run_mirror)
        self.ui.horizontal_btn.clicked.connect(self.run_flip)
        self.ui.checkered_btn.clicked.connect(self.run_checkered)

    def show_e(self):
        self.ui.video_lbl.setPixmap(QPixmap('f.jpg'))

    def run_emoji(self):
        self.em=Emoji()
        self.em.start()
        self.em.set_emoji_signal.connect(self.show_e)


    def run_le(self):
        self.moutheye=EyesMouth()
        self.moutheye.start()
        self.moutheye.set_em_signal.connect(self.show_e)

    def run_mirror(self):
        self.mirror=Mirror()
        self.mirror.start()
        self.mirror.set_mirror_signal.connect(self.show_e)

    def run_flip(self):
        self.flip = Flip()
        self.flip.start()
        self.flip.set_flip_signal.connect(self.show_e)

    def run_checkered(self):
        self.check = Checkered()
        self.check.start()
        self.check.set_check_signal.connect(self.show_e)


if __name__ == "__main__":
    app = QApplication([])
    widget = camera()
    sys.exit(app.exec())
