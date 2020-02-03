# -*- coding: utf-8 -*-

import logging
import os

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication
from fuocore.utils import is_osx, get_osx_theme

logger = logging.getLogger(__name__)


DARK = 'dark'
LIGHT = 'light'


def read_qss(filename):
    filepath = os.path.abspath(__file__)
    dirname = os.path.dirname(filepath)
    qssfilepath = os.path.join(dirname, 'themes/{}'.format(filename))
    with open(qssfilepath, encoding='UTF-8') as f:
        s = f.read()
    return s


class ThemeManager:
    """检测系统主题，自动适配

    **TODO**:

    - 添加 dark 主题
    - 检测系统主题
    """
    def __init__(self, app):
        self._app = app
        self.theme = None

    def autoload(self):
        if self._app.config.THEME == 'auto':
            if is_osx():
                if get_osx_theme() == 1:
                    theme = DARK
                else:
                    theme = LIGHT
            else:
                theme = self.guess_system_theme()
        else:  # user settings have highest priority
            theme = self._app.config.THEME

        if theme == DARK:
            self.load_dark()
        else:
            self.load_light()

        self.theme = theme

    def guess_system_theme(self):
        palette = self._app.palette()
        bg_color = palette.color(QPalette.Window)
        if bg_color.lightness() > 150:
            return LIGHT
        return DARK

    def load_light(self):
        common = read_qss('common.qss')
        light = read_qss('light.qss')
        QApplication.instance().setStyleSheet(common + light)

    def load_dark(self):
        common = read_qss('common.qss')
        dark = read_qss('dark.qss')
        QApplication.instance().setStyleSheet(common + dark)

        # 测试发现，在 macOS dark 模式下，alternate 行的背景色是灰色，
        # 正确的颜色应该类似透明的黑色。我们这里手动给 SongsTableView 处理这种情况。
        # 复现代码见：https://gist.github.com/cosven/0d1f06cb78c79171da51bee9376f71fd
        self._app.ui.songs_table.setStyleSheet(
            "alternate-background-color: rgba(50,50,50,0.2)")
