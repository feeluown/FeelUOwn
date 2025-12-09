import asyncio
import os
from contextlib import contextmanager

from qasync import QEventLoop
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout

from feeluown.debug import *  # noqa


@contextmanager
def simple_qapp():
    qapp = QApplication([])
    yield qapp
    qapp.exec()


@contextmanager
def async_simple_qapp():
    app_close_event = asyncio.Event()
    qapp = QApplication([])
    qapp.aboutToQuit.connect(app_close_event.set)
    yield qapp
    asyncio.run(app_close_event.wait(), loop_factory=QEventLoop)


def read_dark_theme_qss():
    from feeluown.gui.theme import read_resource

    pkg_root_dir = os.path.join(os.path.dirname(__file__), "..")
    icons_dir = os.path.join(pkg_root_dir, "gui/assets/icons")
    QDir.addSearchPath("icons", icons_dir)

    qss = read_resource("common.qss")
    dark = read_resource("dark.qss")
    return qss + "\n" + dark


@contextmanager
def simple_layout(cls=QHBoxLayout, theme="", aio=False):
    func = async_simple_qapp if aio is True else simple_qapp
    with func():
        main = QWidget()
        if theme == "dark":
            main.setStyleSheet(read_dark_theme_qss())
        layout = cls(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        yield layout
        main.show()
