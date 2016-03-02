# -*- coding: utf-8 -*-

from functools import partial

from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton

import asyncio
import requests


class TracksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self._img_label = QLabel(self)
        self._title_label = QLabel('Test love music')
        self._play_all_btn = QPushButton('Play All')

        self._img_label.setObjectName('tracks_img_label')
        self._title_label.setObjectName('tracks_title_label')
        self._play_all_btn.setObjectName('tracks_play_all_btn')
        self._title_label.setAlignment(Qt.AlignCenter)

        self._img_label.setFixedSize(180, 180)
        
        self.layout.addSpacing(20)
        self.layout.addWidget(self._img_label)
        self.layout.addSpacing(15)
        self.layout.addWidget(self._title_label)
        self.layout.addSpacing(10)
        self.layout.addWidget(self._play_all_btn)
        self.layout.addStretch(1)

        self.layout.setContentsMargins(0, 0, 0, 0)

    def load_img(self, url):
        params = "?param={width}y{height}".format(width=180, height=180)
        url += params

        @asyncio.coroutine
        def _set_img():
            app_event_loop = asyncio.get_event_loop()
            future = app_event_loop.run_in_executor(
                None, partial(requests.get, url))
            res = yield from future
            img = QImage()
            img.loadFromData(res.content)
            self._img_label.setPixmap(QPixmap(img))
        asyncio.Task(_set_img())

    def set_title(self, title):
        self._title_label.setText(title)
