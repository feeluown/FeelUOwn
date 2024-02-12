import os
from contextlib import contextmanager
from unittest.mock import MagicMock

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout


@contextmanager
def simple_qapp():
    qapp = QApplication([])
    yield qapp
    qapp.exec()


@contextmanager
def mock_app():
    app = MagicMock()
    yield app


def read_dark_theme_qss():
    from feeluown.gui.theme import read_resource

    pkg_root_dir = os.path.join(os.path.dirname(__file__), '..')
    icons_dir = os.path.join(pkg_root_dir, 'gui/assets/icons')
    QDir.addSearchPath('icons', icons_dir)

    qss = read_resource('common.qss')
    dark = read_resource('dark.qss')
    return qss + '\n' + dark


@contextmanager
def simple_layout(cls=QHBoxLayout, theme=''):
    with simple_qapp():
        main = QWidget()
        if theme == 'dark':
            main.setStyleSheet(read_dark_theme_qss())
        layout = cls(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        yield layout
        main.show()
