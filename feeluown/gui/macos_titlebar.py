import ctypes
import logging
import sys
from ctypes import c_bool, c_char_p, c_long, c_ulong, c_void_p
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtWidgets import QWidget


logger = logging.getLogger(__name__)


@dataclass
class _NSWindowState:
    ns_window: c_void_p
    style_mask: int
    title_visibility: int
    titlebar_appears_transparent: bool
    movable_by_window_background: bool


class MacOSNativeTitlebarMode:
    """Temporarily hide a macOS native titlebar while keeping traffic lights."""

    def __init__(self, widget):
        self._widget = widget if isinstance(widget, QWidget) else None
        self._state: Optional[_NSWindowState] = None

    @property
    def is_supported(self) -> bool:
        return sys.platform == "darwin" and self._widget is not None

    def enter(self):
        if not self.is_supported:
            return
        if self._state is not None:
            self.reapply()
            return
        try:
            ns_window = _get_ns_window(self._widget)
            if not ns_window:
                return
            self._state = _read_state(ns_window)
            _hide_titlebar(ns_window)
        except Exception:  # noqa
            logger.exception("enter macOS native titlebar mode failed")
            self._state = None

    def reapply(self):
        if not self.is_supported or self._state is None:
            return
        try:
            ns_window = _get_ns_window(self._widget)
            if not ns_window:
                return
            if ns_window != self._state.ns_window:
                self._state = _read_state(ns_window)
            _hide_titlebar(ns_window)
        except Exception:  # noqa
            logger.exception("reapply macOS native titlebar mode failed")

    def exit(self):
        if self._state is None:
            return
        state = self._state
        self._state = None
        try:
            _restore_state(state)
        except Exception:  # noqa
            logger.exception("exit macOS native titlebar mode failed")


def _objc():
    objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
    objc.sel_registerName.restype = c_void_p
    objc.sel_registerName.argtypes = [c_char_p]
    return objc


def _sel(name):
    return _objc().sel_registerName(name.encode())


def _msg(receiver, selector, restype=c_void_p, argtypes=(), *args):
    send = _objc().objc_msgSend
    send.restype = restype
    send.argtypes = [c_void_p, c_void_p, *argtypes]
    return send(receiver, _sel(selector), *args)


def _get_ns_window(widget: QWidget):
    return _msg(c_void_p(int(widget.winId())), "window")


def _read_state(ns_window) -> _NSWindowState:
    return _NSWindowState(
        ns_window=ns_window,
        style_mask=_msg(ns_window, "styleMask", c_ulong),
        title_visibility=_msg(ns_window, "titleVisibility", c_long),
        titlebar_appears_transparent=bool(
            _msg(ns_window, "titlebarAppearsTransparent", c_bool)
        ),
        movable_by_window_background=bool(
            _msg(ns_window, "isMovableByWindowBackground", c_bool)
        ),
    )


def _hide_titlebar(ns_window):
    style = _msg(ns_window, "styleMask", c_ulong)
    style |= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 15)
    _msg(ns_window, "setStyleMask:", None, (c_ulong,), style)
    _msg(ns_window, "setTitleVisibility:", None, (c_long,), 1)
    _msg(ns_window, "setTitlebarAppearsTransparent:", None, (c_bool,), True)
    _msg(ns_window, "setMovableByWindowBackground:", None, (c_bool,), True)


def _restore_state(state: _NSWindowState):
    ns_window = state.ns_window
    _msg(ns_window, "setStyleMask:", None, (c_ulong,), state.style_mask)
    _msg(ns_window, "setTitleVisibility:", None, (c_long,), state.title_visibility)
    _msg(
        ns_window,
        "setTitlebarAppearsTransparent:",
        None,
        (c_bool,),
        state.titlebar_appears_transparent,
    )
    _msg(
        ns_window,
        "setMovableByWindowBackground:",
        None,
        (c_bool,),
        state.movable_by_window_background,
    )
