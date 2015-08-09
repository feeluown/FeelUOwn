#!/usr/bin/env python3
# -*- coding: utf-8 -*

import asyncio
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import QMediaPlayer
from constants import ICON_PATH
from base.player import Player
from base.common import singleton
from constants import WINDOW_ICON


@singleton
class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon(WINDOW_ICON))
        self.player = Player()
        self.__menu = QMenu()
        self.__set_actions()
        self.__set_menu()
        self.__init_prop()
        self.__init_signal_binding()

    def __init_signal_binding(self):
        self.activated.connect(self.on_activated)

    def __init_prop(self):
        self.__pause.setIcon(QIcon(ICON_PATH + "pause.png"))

    def __set_actions(self):
        self.__show = QAction(u"显示主窗口", self.__menu)
        self.__show.setIcon(QIcon(WINDOW_ICON))
        self.__show.triggered.connect(self.show_main_widget)
        ###############################################
        self.__user = QAction(self.__menu)  #当前歌曲
        self.__user.setIcon(QIcon(ICON_PATH + "login.png"))
        ###############################################
        self.__pause = QAction(u"播放", self.__menu)    #暂停
        self.__pause.triggered.connect(self.__play_or_pause)
        self.__last = QAction(u"上一首", self.__menu)     #上一曲
        self.__last.setIcon(QIcon(ICON_PATH + "last.png"))
        self.__last.triggered.connect(self.player.play_next)
        self.__next = QAction(u"下一首", self.__menu)     #下一曲
        self.__next.setIcon(QIcon(ICON_PATH + "next.png"))
        self.__next.triggered.connect(self.player.play_last)
        ###############################################
        self.__mode = QMenu(self.__menu)     #播放模式
        self.__mode.setTitle(u"播放模式")

        self.__mode_random = QAction(u"随机随机", self.__mode)
        self.__mode_random.triggered.connect(self.player.set_play_mode_random)

        self.__mode_loop = QAction(u"重复播放", self.__mode)
        self.__mode_loop.triggered.connect(self.player.set_play_mode_loop)

        self.__mode_one_in_loop = QAction(u"单曲循环", self.__mode)
        self.__mode_one_in_loop.triggered.connect(self.player.set_play_mode_one_in_loop)


        self.__minimize = QMenu(self.__menu)     #最小化
        self.__minimize.setTitle("Minimize")
        ###############################################
        self.__close_lyrics = QAction("Close Lyrics", self.__menu)   #关闭歌词
        self.__lock__lyrics = QAction("Lock Lyrics", self.__menu)   #锁定歌词
        ###############################################
        self.__settings = QAction("Settings", self.__menu)  #系统设置
        ###############################################
        self.__quit = QAction("Quit", self.__menu)  #退出
        self.__quit.triggered.connect(self.quit_app)


    def paintEventE(self, QPaintEvent):
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

    def quit_app(self):
        APP_EVENT_LOOP = asyncio.get_event_loop()
        APP_EVENT_LOOP.stop()
        QApplication.exit(0)
        sys.exit(0)

    def __play_or_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.__pause.setIcon(QIcon(ICON_PATH + "pause.png"))
            self.__pause.setText('play')
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()
            self.__pause.setIcon(QIcon(ICON_PATH + "play.png"))
            self.__pause.setText('pause')

    def __set_menu(self):
        self.__menu.addAction(self.__show)
        self.__menu.addSeparator()
        self.__menu.addAction(self.__pause)
        self.__menu.addAction(self.__last)
        self.__menu.addAction(self.__next)
        self.__menu.addSeparator()

        self.__menu.addMenu(self.__mode)
        self.__mode.addAction(self.__mode_loop)
        self.__mode.addAction(self.__mode_one_in_loop)
        self.__mode.addAction(self.__mode_random)
        self.__menu.addMenu(self.__minimize)
        self.__menu.addSeparator()

        # self.__menu.addAction(self.__close_lyrics)
        # self.__menu.addAction(self.__lock__lyrics)
        # self.__menu.addSeparator()
        #
        # self.__menu.addAction(self.__settings)
        # self.__menu.addSeparator()

        self.__menu.addAction(self.__quit)
        self.setContextMenu(self.__menu)

    def show_main_widget(self):
        pw = self.get_main_widget()
        if pw.isVisible():
            pw.hide()
        else:
            pw.show()

    def get_main_widget(self):
        return self.parent()

    @pyqtSlot(QMediaPlayer.State)
    def on_player_state_changed(self, state):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.__pause.setIcon(QIcon(ICON_PATH + "play.png"))
            self.__pause.setText('pause')
        elif self.player.state() == QMediaPlayer.PausedState:
            self.__pause.setIcon(QIcon(ICON_PATH + "pause.png"))
            self.__pause.setText('play')

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick or reason == QSystemTrayIcon.Trigger:
            self.show_main_widget()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    t = TrayIcon()
    t.show()
    sys.exit(app.exec_())
