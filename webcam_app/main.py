# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication, QWidget,QInputDialog,QLineEdit
from PySide6.QtGui import *
from PySide6 import QtGui
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QThread, Signal, QDir
from instabot import Bot
from threading import Thread
import cv2
from PIL.ImageQt import ImageQt
from PIL import Image


def convertCVImage2QtImage(cv_img):
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    height, width, channel = cv_img.shape
    bytesPerLine = 3 * width
    qimg = QImage(cv_img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class Checkered(QThread):
    signal_show_frame = Signal(object)

    def __init__(self):
        super(Checkered, self).__init__()

    def run(self):
        self.video = cv2.VideoCapture(0)

        face_detector = cv2.CascadeClassifier('fd.xml')
        while True:
            valid, self.frame = self.video.read()
            if valid is not True:
                break
            frame_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(frame_gray, 3.1)

            for face in faces:
                x, y, w, h = face
                image_face = self.frame[y:y + h, x:x + w]
                org_checkered = cv2.resize(image_face, (0, 0), fx=0.1, fy=0.1, interpolation=cv2.INTER_LINEAR)
                resized_checkered = cv2.resize(org_checkered, (w, h), interpolation=cv2.INTER_NEAREST)
                self.frame[y:y + h, x:x + w] = resized_checkered
            self.signal_show_frame.emit(self.frame)
            cv2.waitKey(30)

    def stop(self):
        try:
            self.video.release()
        except:
            pass

class Flip(QThread):
    set_flip_signal = Signal(object)

    def __init__(self):
        super(Flip, self).__init__()

    def run(self):
        self.video = cv2.VideoCapture(0)
        while True:
            valid, self.frame = self.video.read()
            if valid is not True:
                break

            right=self.frame[0:self.frame.shape[0],0:self.frame.shape[1]//2]
            left=self.frame[0:self.frame.shape[0],self.frame.shape[1]//2:self.frame.shape[1]]
            left=cv2.flip(left,0)
            self.frame[0:self.frame.shape[0],self.frame.shape[1]//2:self.frame.shape[1]]=left
            self.set_flip_signal.emit(self.frame)
            cv2.waitKey(30)
    def stop(self):
        try:
            self.video.release()
        except:
            pass

class Mirror(QThread):
    set_mirror_signal = Signal(object)

    def __init__(self):
        super(Mirror, self).__init__()

    def run(self):
        self.video = cv2.VideoCapture(0)
        while True:
            valid, self.frame = self.video.read()
            if valid is not True:
                break
            (r, c, ch) = self.frame.shape
            left = self.frame[0:r, 0:c // 2]
            self.frame[0:r, c // 2:c] = cv2.flip(left, 1)
            self.set_mirror_signal.emit(self.frame)
            cv2.waitKey(30)

    def stop(self):
        try:
            self.video.release()
        except:
            pass


class Emoji(QThread):
    set_emoji_signal = Signal(object)

    def __init__(self):
        super(Emoji, self).__init__()

    def run(self):
        self.video = cv2.VideoCapture(0)
        face_detector = cv2.CascadeClassifier('fd.xml')
        emoji = cv2.imread('emoji.png', cv2.IMREAD_UNCHANGED)
        st_emoji = emoji[:, :, 0:3]
        st_emoji_gray = cv2.cvtColor(st_emoji, cv2.COLOR_RGB2GRAY)
        mask = emoji[:, :, 3]
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        while True:
            valid, self.frame = self.video.read()
            if valid is not True:
                break
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 3.1)
            for face in faces:
                x, y, w, h = face
                img_face = self.frame[y:y + h, x:x + w]
                st_emoji_resized = cv2.resize(st_emoji, (w, h))
                mask_resized = cv2.resize(mask, (w, h))
                st_emoji_resized = st_emoji_resized.astype(float) / 255
                mask_resized = mask_resized.astype(float) / 255
                img_face = img_face.astype(float) / 255
                forg = cv2.multiply(mask_resized, st_emoji_resized)
                back = cv2.multiply(img_face, 1 - mask_resized)
                res = cv2.add(back, forg)
                res *= 255
                self.frame[y:y + h, x:x + w] = res
            # result=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)
            self.set_emoji_signal.emit(self.frame)
            cv2.waitKey(30)


    def stop(self):
        try:
            self.video.release()
        except:
            pass


class EyesMouth(QThread):
    set_em_signal = Signal(object)

    def __init__(self):
        super(EyesMouth, self).__init__()

    def run(self):
        self.video = cv2.VideoCapture(0)
        eyes_sticker= cv2.imread('eyes_emj.png',cv2.IMREAD_UNCHANGED)
        eyes_sticker_org = eyes_sticker[:, :, 0:3]
        #eyes_sticker_gray = cv2.cvtColor(eyes_sticker_org, cv2.COLOR_RGB2GRAY)
        eyes_mask=eyes_sticker[:, :, 3]
        eyes_mask = cv2.cvtColor(eyes_mask, cv2.COLOR_GRAY2BGR)

        mouth_sticker = cv2.imread('lip.png',cv2.IMREAD_UNCHANGED)
        mouth_sticker_org = mouth_sticker[:, :, 0:3]
        #mouth_sticker_gray = cv2.cvtColor(mouth_sticker_org, cv2.COLOR_RGB2GRAY)
        mouth_mask = mouth_sticker[:, :, 3]
        mouth_mask = cv2.cvtColor(mouth_mask, cv2.COLOR_GRAY2BGR)

        face_detector = cv2.CascadeClassifier('fd.xml')
        eye_detector = cv2.CascadeClassifier('parojosG.xml')
        lip_detector = cv2.CascadeClassifier('haarcascade_smile.xml')
        while True:
            valid, self.frame = self.video.read()
            if valid is not True:
                break

            #gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(self.frame, 3.1)
            for face in faces:
                x, y, w, h = face
                eyes = eye_detector.detectMultiScale(self.frame[y:y + h, x:x + w], 3.1)
                lips = lip_detector.detectMultiScale(self.frame[y:y + h, x:x + w], 3.3)
                for lip in lips:
                    xl, yl, wl, hl = lip
                    img_lip = self.frame[y +yl:y + yl + hl, x + xl:x + xl + wl]
                    mouth_sticker_resized = cv2.resize(mouth_sticker_org, (wl, hl))
                    mouth_mask_resized=cv2.resize(mouth_mask,(wl,hl))
                    mouth_mask_resized = mouth_mask_resized.astype(float) / 255
                    mouth_sticker_resized = mouth_sticker_resized.astype(float) / 255
                    img_lip=img_lip.astype(float)/255
                    forg = cv2.multiply(mouth_mask_resized, mouth_sticker_resized)
                    back = cv2.multiply(img_lip, 1 - mouth_mask_resized)
                    res = cv2.add(back, forg)
                    res *= 255
                    self.frame[y +yl:y + yl + hl, x + xl:x + xl + wl] = res

                for eye in eyes:
                    xe, ye, we, he = eye
                    img_eye = self.frame[y +ye:y + ye + he, x + xe:x + xe + we]
                    eye_sticker_resized = cv2.resize(eyes_sticker_org, (we, he))
                    eye_mask_resized = cv2.resize(eyes_mask, (we, he))
                    eye_mask_resized = eye_mask_resized.astype(float) / 255
                    eye_sticker_resized = eye_sticker_resized.astype(float) / 255
                    img_eye = img_eye.astype(float) / 255
                    forg = cv2.multiply(eye_sticker_resized,eye_mask_resized)
                    back = cv2.multiply(img_eye, 1 - eye_mask_resized)
                    res = cv2.add(back, forg)
                    res *= 255
                    self.frame[y + ye:y + ye + he, x + xe:x + xe + we] =res
                # result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            self.set_em_signal.emit(self.frame)
            cv2.waitKey(30)

    def stop(self):
        try:
            self.video.release()
        except:
            pass

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
        self.ui.shot_btn.clicked.connect(self.save_image)

        # threads
        self.thread_emoji = Emoji()
        self.thread_emoji.set_emoji_signal.connect(self.show_e)
        self.thread_mouth_eye = EyesMouth()
        self.thread_mouth_eye.set_em_signal.connect(self.show_e)
        self.thread_check = Checkered()
        self.thread_check.signal_show_frame.connect(self.show_e)
        self.thread_mirror=Mirror()
        self.thread_mirror.set_mirror_signal.connect(self.show_e)
        self.thread_flip=Flip()
        self.thread_flip.set_flip_signal.connect(self.show_e)

    def terminateAllThreads(self):
        self.thread_emoji.stop()
        self.thread_mouth_eye.stop()
        self.thread_check.stop()
        self.thread_mirror.stop()
        self.thread_flip.stop()

    def show_e(self, img):
        res_img = convertCVImage2QtImage(img)
        self.ui.video_lbl.setPixmap(res_img)

    def run_emoji(self):
        self.terminateAllThreads()
        self.thread_emoji.start()

    def run_le(self):
        self.terminateAllThreads()
        self.thread_mouth_eye.start()

    def run_mirror(self):
        self.terminateAllThreads()
        self.thread_mirror.start()

    def run_flip(self):
        self.terminateAllThreads()
        self.thread_flip.start()


    def run_checkered(self):
        self.terminateAllThreads()
        self.thread_check.start()

    def save_image(self):
        if self.thread_emoji.isRunning():
            cv2.imwrite('out.jpg',self.thread_emoji.frame)
        elif self.thread_flip.isRunning():
            cv2.imwrite('out.jpg', self.thread_flip.frame)
        elif self.thread_mirror.isRunning():
            cv2.imwrite('out.jpg', self.thread_mirror.frame)
        elif self.thread_check.isRunning():
            cv2.imwrite('out.jpg', self.thread_check.frame)
        elif self.thread_mouth_eye.isRunning():
            cv2.imwrite('out.jpg',self.thread_mouth_eye.frame)
        username, ok = QInputDialog().getText(self, "Instagram Login",
                                     "User name:", QLineEdit.Normal,
                                     "")
        if ok and username:
            password, ok = QInputDialog().getText(self, "Instagram Login",
                                              "Password:", QLineEdit.Normal,"")
            if ok and password:
                caption, ok = QInputDialog().getText(self, "Post caption",
                                                      "Caption:", QLineEdit.Normal, "")
                if ok and caption:
                    bot = Bot()
                    bot.login(username=username, password=password)
                    bot.upload_photo("out.jpg", caption=caption)


if __name__ == "__main__":
    app = QApplication([])
    widget = camera()
    sys.exit(app.exec())
