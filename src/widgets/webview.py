# -*- coding: utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from setting import MODE, PUBLIC_PATH, DEBUG
import json


class WebView(QWebView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init()
        self.loadFinished.connect(self.on_load_finished)

    def init(self):
        if MODE == DEBUG:
            self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

    def load_css(self):
        all_css = QFileInfo(PUBLIC_PATH + 'all.css').absoluteFilePath()
        self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(all_css))

    @pyqtSlot()
    def on_load_finished(self):
        print('finish')
        print(self.page())
        a = {'a': 'hello'}
        self.page().mainFrame().evaluateJavaScript('')

    def run_js_interface(self, data=None):
        """

        :param data: string, such as json.dumps(dict)
        :return:
        """
        pass