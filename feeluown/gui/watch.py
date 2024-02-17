import logging
from enum import IntEnum
from typing import TYPE_CHECKING, cast

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.gui.helpers import esc_hide_widget
from feeluown.gui.widgets.frameless import ResizableFramelessContainer

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class Mode(IntEnum):
    none = 0    # Hide all video related widgets, including controller buttons.
    fullwindow = 1  # Show video widget inside the full window coantainer.
    pip = 2     # Show video widget in a detached container (picture in picture).


class FullWindowContainer(QWidget):
    def __init__(self, app: 'GuiApp', parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._app.installEventFilter(self)
        esc_hide_widget(self)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def set_body(self, widget):
        self._layout.insertWidget(0, widget)

    def showEvent(self, e):
        self.resize(self._app.size())
        super().showEvent(e)

    def eventFilter(self, obj, event):
        if self.isVisible() and obj is self._app and event.type() == QEvent.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return False


class WatchManager:
    def __init__(self, app: 'GuiApp'):
        """video view controller

        :type app: feeluown.app.App
        :type ui: feeluown.ui.Ui
        """
        self._app = app
        self._pip_container = ResizableFramelessContainer()
        self._fullwindow_container = FullWindowContainer(app, parent=app)

        #: Is the video widget visible before.
        self._is_visible_before_auto_set_to_none = False

    def initialize(self):
        self._initialize_mpv_video_renderring()

        self._ui = self._app.ui
        self._ui.pc_panel.media_btns.toggle_video_btn.clicked.connect(
            lambda: self.set_mode(Mode.fullwindow))
        self._app.player.media_changed.connect(self.on_media_changed, aioqueue=True)
        self._app.player.video_channel_changed.connect(self.on_video_channel_changed, aioqueue=True)  # noqa

        self._pip_container.setMinimumSize(200, 130)
        self._pip_container.hide()
        self._fullwindow_container.hide()

    def set_mode(self, mode):
        mode = Mode(mode)  # So that user can call set_mode(0/1/2) in REPL.
        if mode is Mode.none:
            self.exit_fullwindow_mode()
            self.exit_pip_mode()
        else:
            # change current mode to mode
            #
            # if mode is same as the current mode, exit mode
            # if mode is not same as the current mode, exit
            # current mode and enter mode
            if mode is Mode.fullwindow:
                self.exit_pip_mode()
                self.enter_fullwindow_mode(go_back=self.exit_fullwindow_mode)
            else:
                self.exit_fullwindow_mode()
                self.enter_pip_mode()

    def enter_fullwindow_mode(self, go_back=None):
        video_widget = self._app.ui.mpv_widget
        logger.debug("enter video-show fullwindow mode")
        if video_widget.parent() != self._fullwindow_container:
            with video_widget.change_parent():
                self._fullwindow_container.set_body(video_widget)

        self._fullwindow_container.show()
        self._fullwindow_container.raise_()
        video_widget.show()
        video_widget.overlay_auto_visible = True
        video_widget.ctl_bar.clear_adhoc_btns()
        pip_btn = video_widget.ctl_bar.add_adhoc_btn('画中画')
        pip_btn.clicked.connect(lambda: self.set_mode(Mode.pip))
        if go_back is not None:
            hide_btn = video_widget.ctl_bar.add_adhoc_btn('最小化')
            hide_btn.clicked.connect(go_back)

    def exit_fullwindow_mode(self):
        self._app.ui.mpv_widget.hide()
        self._fullwindow_container.hide()
        logger.debug("exit video-show fullwindow mode")

    def _is_pip_mode(self):
        return self._app.ui.mpv_widget.parent() == self._pip_container

    def _is_fullwindow_mode(self):
        return (self._app.ui.mpv_widget.parent() == self._app and
                self._app.ui.mpv_widget.isVisible())

    def _is_none_mode(self):
        return not (self._is_pip_mode() or self._is_fullwindow_mode())

    def enter_pip_mode(self):
        """enter picture in picture mode"""
        logger.debug("enter video-show picture in picture mode")
        video_widget = self._app.ui.mpv_widget
        video_widget.overlay_auto_visible = True

        if video_widget.parent() != self._pip_container:
            with video_widget.change_parent():
                self._pip_container.attach_widget(video_widget)

        video_widget.ctl_bar.clear_adhoc_btns()
        fullscreen_btn = video_widget.ctl_bar.add_adhoc_btn('全屏')
        hide_btn = video_widget.ctl_bar.add_adhoc_btn('退出画中画')
        fullscreen_btn.clicked.connect(self.toggle_pip_fullscreen)
        hide_btn.clicked.connect(lambda: self.set_mode(Mode.fullwindow))
        self._pip_container.show()
        self._app.ui.mpv_widget.show()
        try:
            width = int(self._app.player._mpv.width)  # type: ignore
            height = int(self._app.player._mpv.height)  # type: ignore
        except ValueError:
            logger.exception('mpv video width/height is not a valid int')
        else:
            proper_width = max(min(width, 640), 320)
            proper_height = height * proper_width // width
            self._pip_container.resize(proper_width, proper_height)

    def exit_pip_mode(self):
        """exit picture in picture mode"""
        self._pip_container.hide()
        logger.debug("exit video-show picture in picture mode")

    def toggle_pip_fullscreen(self):
        self._pip_container.setWindowState(
            self._pip_container.windowState() ^ Qt.WindowFullScreen)

    def play_video(self, video):
        self._app.playlist.set_current_model(video)
        self.set_mode(Mode.fullwindow)

    def on_media_changed(self, media):
        if not media:
            logger.debug('media is changed to none, hide video-show')
            self.set_mode(Mode.none)

    def on_video_channel_changed(self, _):
        if bool(self._app.player.video_channel) is False:
            # When the mpv widget is changing it's parent, the video_channel may be
            # changed to empty manully (see mpv_widget.change_parent).
            if not self._app.ui.mpv_widget.is_changing_parent:
                return

            # HELP(cosven): Even if player play a valid video, the video_format
            # is changed to none first, and then it is changed to the real value.
            # So check if the video widget is visible before hide it.
            self._is_visible_before_auto_set_to_none = self._app.ui.mpv_widget.isVisible()  # noqa
            self.set_mode(Mode.none)
        else:
            if self._is_visible_before_auto_set_to_none is True:
                if self._is_fullwindow_mode():
                    self.set_mode(Mode.fullwindow)
                elif self._is_pip_mode():
                    self.set_mode(Mode.pip)

    #
    # private methods
    #
    def _initialize_mpv_video_renderring(self):
        # HACK: Show mpv_widget once to initialize mpv video renderring correctly.
        # Remember to set aioqueue to true so that mpv_widget is hidden after the
        # app(Qt) event loop is started.
        self._app.ui.mpv_widget.show()
        self._app.started.connect(lambda *_: self._app.ui.mpv_widget.hide(), weak=False)
