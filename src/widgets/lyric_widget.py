# -*- coding:utf8 -*-
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from base.common import singleton


class LyricWidget(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.drag_pos = (0, 0)
        self.__init_attr()

        self.__lyrics = []
        self.__translate_lyric = []
        self.__time_sequence = []
        # self.show()
        self.close()

    def __init_attr(self):
        height = 60
        width = 800
        self.setMouseTracking(False)
        self.setObjectName('lyric_label')
        self.setAlignment(Qt.AlignCenter)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(0.5)

        self.resize(width, height)
        self.move((QApplication.desktop().width() - width)/2, 40)

    def reset_lyric(self):
        self.__lyrics = []
        self.__translate_lyric = []
        self.__time_sequence = []

    def set_lyric(self, lyric_model):
        self.__time_sequence = lyric_model['time_sequence']
        self.__lyrics = lyric_model['lyric']
        self.__translate_lyric = lyric_model['translate_lyric']

    def has_lyric(self):
        if self.__lyrics:
            return True
        return False

    def sync_lyric(self, ms):
        if self.has_lyric():
            for i, each in enumerate(self.__time_sequence):
                if ms >= each:
                    lyric = self.__lyrics[i][:-1]
                    if self.__translate_lyric:
                        tlyric = self.__translate_lyric[i][:-1]
                        lyric += "\n" + tlyric
                    self.setText(lyric)
    #
    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         self.drag_pos = event.globalPos() - self.pos()
    #     event.accept()
    #
    # def mouseMoveEvent(self, event):
    #     if event.buttons() == Qt.LeftButton:
    #         self.move(event.globalPos() - self.drag_pos)
    #         event.accept()
    #     if event.buttons() == Qt.RightButton:
    #         event.ignore()