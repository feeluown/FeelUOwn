"""macOS PyQt6: native traffic-light buttons, hidden titlebar.

Run: uv run --extra qt python examples/macos_native_titlebar.py
"""

import ctypes
import sys
from ctypes import c_bool, c_char_p, c_long, c_ulong, c_void_p

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
objc.sel_registerName.restype = c_void_p
objc.sel_registerName.argtypes = [c_char_p]


def sel(name):
    return objc.sel_registerName(name.encode())


def msg(receiver, selector, restype=c_void_p, argtypes=(), *args):
    send = objc.objc_msgSend
    send.restype = restype
    send.argtypes = [c_void_p, c_void_p, *argtypes]
    return send(receiver, sel(selector), *args)


def expand_client_area(widget):
    for name in ("ExpandedClientAreaHint", "NoTitleBarBackgroundHint"):
        flag = getattr(Qt.WindowType, name, None)
        if flag is not None:
            widget.setWindowFlag(flag, True)
    attr = getattr(Qt.WidgetAttribute, "WA_ContentsMarginsRespectsSafeArea", None)
    if attr is not None:
        widget.setAttribute(attr, False)


def make_titlebar_transparent(widget):
    ns_window = msg(c_void_p(int(widget.winId())), "window")
    style = msg(ns_window, "styleMask", c_ulong)
    style |= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 15)
    msg(ns_window, "setStyleMask:", None, (c_ulong,), style)
    msg(ns_window, "setTitleVisibility:", None, (c_long,), 1)
    msg(ns_window, "setTitlebarAppearsTransparent:", None, (c_bool,), True)
    msg(ns_window, "setMovableByWindowBackground:", None, (c_bool,), True)


class Toolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(38)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(86, 0, 12, 0)
        layout.setSpacing(8)
        layout.addWidget(QLabel("Toolbar at y=0"), 0, Qt.AlignmentFlag.AlignTop)
        layout.addStretch()
        for text in ("Back", "Forward", "Search"):
            button = QPushButton(text)
            button.setFixedHeight(28)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)

    def mousePressEvent(self, event):
        window = self.window().windowHandle()
        if event.button() == Qt.MouseButton.LeftButton and window is not None:
            if window.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)


def main():
    if sys.platform != "darwin":
        print("This demo is macOS-only.")
        return 1

    app = QApplication(sys.argv)
    window = QWidget()
    expand_client_area(window)
    window.setWindowTitle("Hidden titlebar")
    window.resize(720, 420)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(Toolbar())

    body = QLabel("Native buttons are kept; the titlebar is not visible.")
    body.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(body, 1)

    window.show()
    QTimer.singleShot(0, lambda: make_titlebar_transparent(window))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
