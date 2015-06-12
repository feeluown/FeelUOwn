# -*- coding: utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from setting import PUBLIC_PATH
import json



testJs = """
window.python_log(%s);
"""


class WebView(QWebView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_css()
        self.init()
        self.loadFinished.connect(self.on_load_finished)

    def init(self):
        self.configure()

    def load_css(self):
        all_css = QFileInfo(PUBLIC_PATH + 'all.css').absoluteFilePath()
        print(all_css)
        # self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(all_css))

    def configure(self):
        self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

    @pyqtSlot()
    def on_load_finished(self):
        print('finish')
        print(self.page())
        a = {'a': 'hello'}
        self.page().mainFrame().evaluateJavaScript(testJs % json.dumps(a))