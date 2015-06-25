# -*- coding: utf8 -*-
import json

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings

from setting import MODE, PUBLIC_PATH, DEBUG, HTML_PATH


class WebView(QWebView):
    """

    """

    """这个类的实例可能发出的信号。（也就是说，controller只能绑定这些信号，其他信号尽量不要绑定）
    loadProgress(int)
    """
    signal_play = pyqtSignal([int])
    signal_play_playlist = pyqtSignal([int])

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init()

        self.js_queue = []  # 保存页面load完，要执行的js代码

    def init(self):
        self.init_singal_binding()
        if MODE == DEBUG:
            self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)

    def init_singal_binding(self):
        self.loadFinished.connect(self.on_load_finished)

    def load_css(self):
        all_css = QFileInfo(PUBLIC_PATH + 'all.css').absoluteFilePath()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(all_css))

    @pyqtSlot()
    def on_load_finished(self):
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)
        for js_code in self.js_queue:
            self.page().mainFrame().evaluateJavaScript(js_code)
        self.js_queue.clear()

    """给js调用的函数, 需要加上pyqtSlot装饰器
    """
    @pyqtSlot(int)
    def play(self, mid):
        """
        """
        self.signal_play.emit(mid)

    @pyqtSlot(int)
    def play_playlist(self, pid):
        self.signal_play_playlist.emit(pid)

    def run_js_interface(self, data=None):
        """

        :param data: string, such as json.dumps(dict)
        :return:
        """
        pass

    """下面都是给controller调用的函数，最好不要在其他地方调用
    """
    def load_playlist(self, playlist_data):
        """
        :param playlist_data:
        :return:
        """
        data = json.dumps(playlist_data)
        path = QFileInfo(HTML_PATH + 'playlist.html').absoluteFilePath()
        js_code = 'window.fill_playlist(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)

    def load_search_result(self, songs):
        data = json.dumps(songs)
        path = QFileInfo(HTML_PATH + 'search.html').absoluteFilePath()
        js_code = 'window.fill_search(%s)' % data
        self.js_queue.append(js_code)
        self.load(QUrl.fromLocalFile(path))
        self.page().mainFrame().addToJavaScriptWindowObject('js_python', self)