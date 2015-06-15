#!/usr/bin/env python3
# -*- coding: utf-8 -*

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import QMediaPlayer
from setting import ICON_PATH
from base.player import Player


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(ICON_PATH + "format.png"))
        self.player = Player()
        self.__menu = QMenu()
        self.__set_actions()
        self.__set_menu()

    def __set_actions(self):
        self.__user = QAction(self.__menu)  #当前歌曲
        self.__user.setIcon(QIcon(ICON_PATH + "login.png"))
        ###############################################
        self.__pause = QAction("Pause", self.__menu)    #暂停
        self.__pause.triggered.connect(self.__play_or_pause)
        self.__last = QAction("Last Song", self.__menu)     #上一曲
        self.__last.setIcon(QIcon(ICON_PATH + "last.png"))
        self.__last.triggered.connect(self.player.play_next)
        self.__next = QAction("Next Song", self.__menu)     #下一曲
        self.__next.setIcon(QIcon(ICON_PATH + "next.png"))
        self.__next.triggered.connect(self.player.play_last)
        ###############################################
        self.__mode = QMenu(self.__menu)     #播放模式
        self.__mode.setTitle("Play Mode")
        self.__minimize = QMenu(self.__menu)     #最小化
        self.__minimize.setTitle("Minimize")
        ###############################################
        self.__close_lyrics = QAction("Close Lyrics", self.__menu)   #关闭歌词
        self.__lock__lyrics = QAction("Lock Lyrics", self.__menu)   #锁定歌词
        ###############################################
        self.__settings = QAction("Settings", self.__menu)  #系统设置
        ###############################################
        self.__quit = QAction("Quit", self.__menu)  #退出
        self.__quit.triggered.connect(QApplication.quit)

    def paintEvent(self, QPaintEvent):
        """
        self is derived from QWidget, Stylesheets don't work unless \
        paintEvent is reimplemented.
        at the same time, if self is derived from QFrame, this isn't needed.
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __play_or_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.__pause.setIcon(QIcon(ICON_PATH + "pause.png"))
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()
            self.__pause.setIcon(QIcon(ICON_PATH + "play.png"))
        else:
            pass

    def __set_menu(self):
        self.__menu.addAction(self.__pause)
        self.__menu.addAction(self.__last)
        self.__menu.addAction(self.__next)
        self.__menu.addSeparator()

        self.__menu.addMenu(self.__mode)
        self.__menu.addMenu(self.__minimize)
        self.__menu.addSeparator()

        self.__menu.addAction(self.__close_lyrics)
        self.__menu.addAction(self.__lock__lyrics)
        self.__menu.addSeparator()

        self.__menu.addAction(self.__settings)
        self.__menu.addSeparator()

        self.__menu.addAction(self.__quit)
        self.setContextMenu(self.__menu)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    t = TrayIcon()
    t.show()
    sys.exit(app.exec_())
