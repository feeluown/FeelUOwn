# -*- coding: utf-8 -*-

import logging
import os

from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ThemeManager:
    def __init__(self, app):
        self._app = app

    def load_light(self):
        filepath = os.path.abspath(__file__)
        dirname = os.path.dirname(filepath)
        qssfilepath = os.path.join(dirname, 'light.qss')
        with open(qssfilepath) as f:
            s = f.read()
            QApplication.instance().setStyleSheet(s)

    def load_dark(self):
        pass
