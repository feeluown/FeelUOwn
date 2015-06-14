# -*- coding:utf8 -*-
__author__ = 'cosven'

import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import *


from widgets.login_dialog import LoginDialog
from widgets.playlist_widget import PlaylistWidget, PlaylistItem

from views import UiMainWidget
from base.models import DataModel
from base.player import Player
from api import Api, get_url_type


class MainWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # set app name before mediaObject was created to avoid phonon problem
        # QCoreApplication.setApplicationName("NetEaseMusic-ThirdParty")
        self.ui = UiMainWidget()    # 那些widget对象都通过self.ui.*.*来访问，感觉也不是很好

        self.ui.setup_ui(self)

        self.webview = self.ui.right_widget.webview     # 常用的对象复制一下，方便使用
        self.progress = self.ui.top_widget.progress_info

        self.api = Api()
        self.init()

        self.state = {'is_login': False}

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

    def init(self):
        self.init_signal_binding()
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.resize(960, 580)

    def init_signal_binding(self):
        """初始化部分信号绑定
        :return:
        """
        self.ui.top_widget.login_btn.clicked.connect(self.pop_login)
        self.webview.loadProgress.connect(self.on_webview_progress)

    """这部分写一些交互逻辑
    """
    def show_user_playlist(self):
        playlists = self.api.get_user_playlist()
        for playlist in playlists:
            w = PlaylistItem(self)
            w.set_playlist_item(playlist)

            # 感觉这句话增加了耦合度, 暂时没找到好的解决办法
            w.signal_text_btn_clicked.connect(self.on_playlist_btn_clicked)

            if self.api.is_playlist_mine(playlist):
                self.ui.left_widget.central_widget.create_list_widget.layout.addWidget(w)
            else:
                self.ui.left_widget.central_widget.collection_list_widget.layout.addWidget(w)

    """这部分写 pyqtSlot
    """
    @pyqtSlot()
    def pop_login(self):
        if self.state['is_login'] is False:
            w = LoginDialog(self)
            w.signal_login_sucess.connect(self.on_login_success)
            w.show()

    @pyqtSlot(dict)
    def on_login_success(self, data):
        """
        登陆成功
        :param data:
        :return:
        """
        self.state['is_login'] = True

        self.show_user_playlist()

    @pyqtSlot(int)
    def on_playlist_btn_clicked(self, pid):
        playlist_detail = self.api.get_playlist_detail(pid)

        self.webview.load_playlist(playlist_detail)

    @pyqtSlot(int)
    def on_webview_progress(self, percent):
        self.progress.setValue(percent)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    musicbox = MainWidget()
    musicbox.show()
    sys.exit(app.exec_())
