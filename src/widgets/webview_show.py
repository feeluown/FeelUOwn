# -*- coding: utf8 -*-

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from setting import PUBLIC_PATH


class WebView(QWebView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_css()

    def load_css(self):
        all_css = QFileInfo(PUBLIC_PATH + 'all.css').absoluteFilePath()
        print(all_css)
        # self.settings().setUserStyleSheetUrl(QUrl.fromLocalFile(all_css))
