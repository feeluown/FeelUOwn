import logging
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt

from feeluown.gui.widgets.frameless import ResizableFramelessContainer

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


class Mode(IntEnum):
    none = 0    # Hide all video related widgets, including controller buttons.
    normal = 1  # Show video widget inside the main window.
    pip = 2     # Show video widget in a detached container (picture in picture).


class WatchManager:
    def __init__(self, app: 'GuiApp'):
        """video view controller

        :type app: feeluown.app.App
        :type ui: feeluown.ui.Ui
        """
        self._app = app
        self._pip_container = ResizableFramelessContainer()

        #: Is the video widget visible before.
        self._is_visible_before = False

    def initialize(self):
        self._initialize_mpv_video_renderring()

        self._ui = self._app.ui
        self._ui.pc_panel.mv_btn.clicked.connect(self.play_mv)
        self._ui.pc_panel.media_btns.toggle_video_btn.clicked.connect(
            lambda: self.set_mode(Mode.normal))
        self._app.player.media_changed.connect(self.on_media_changed, aioqueue=True)
        self._app.player.video_format_changed.connect(self.on_video_format_changed, aioqueue=True)  # noqa

        self._pip_container.setMinimumSize(200, 130)
        self._pip_container.hide()

    def set_mode(self, mode):
        self._is_visible_before = self._app.ui.mpv_widget.isVisible()
        mode = Mode(mode)  # So that user can call set_mode(0/1/2) in REPL.
        if mode is Mode.none:
            self.exit_normal_mode()
            self.exit_pip_mode()
        else:
            self.enter_mode(mode)

    def enter_mode(self, mode):
        # change current mode to mode
        #
        # if mode is same as the current mode, exit mode
        # if mode is not same as the current mode, exit
        # current mode and enter mode
        if mode is Mode.normal:
            self.exit_pip_mode()
            self.enter_normal_mode()
        else:
            self.exit_normal_mode()
            self.enter_pip_mode()

    def _hide_app_other_widgets(self):
        for widget in (self._app.ui.bottom_panel,
                       self._app.ui._top_separator,
                       self._app.ui._splitter,
                       self._app.ui.top_panel,):
            widget.hide()

    def _show_app_other_widgets(self):
        for widget in (self._app.ui.bottom_panel,
                       self._app.ui._top_separator,
                       self._app.ui._splitter,
                       self._app.ui.top_panel,):
            widget.show()

    def enter_normal_mode(self):
        """enter normal mode"""
        video_widget = self._app.ui.mpv_widget
        logger.info("enter video-show normal mode")
        self._hide_app_other_widgets()

        if video_widget.parent() != self._app:
            layout = self._app.layout()
            layout.insertWidget(1, video_widget)  # type: ignore

        video_widget.show()
        video_widget.overlay_auto_visible = True
        video_widget.ctl_bar.clear_adhoc_btns()
        pip_btn = video_widget.ctl_bar.add_adhoc_btn('画中画')
        hide_btn = video_widget.ctl_bar.add_adhoc_btn('最小化')
        pip_btn.clicked.connect(lambda: self.set_mode(Mode.pip))
        hide_btn.clicked.connect(self.exit_normal_mode)

    def exit_normal_mode(self):
        self._app.ui.mpv_widget.hide()
        self._show_app_other_widgets()
        logger.info("exit video-show normal mode")

    def _is_pip_mode(self):
        return self._app.ui.mpv_widget.parent() == self._pip_container

    def _is_normal_mode(self):
        return (self._app.ui.mpv_widget.parent() == self._app and
                self._app.ui.mpv_widget.isVisible())

    def _is_none_mode(self):
        return not (self._is_pip_mode() or self._is_normal_mode())

    def enter_pip_mode(self):
        """enter picture in picture mode"""
        logger.info("enter video-show picture in picture mode")
        video_widget = self._app.ui.mpv_widget
        video_widget.overlay_auto_visible = True

        if video_widget.parent() != self._pip_container:
            self._pip_container.attach_widget(self._app.ui.mpv_widget)

        video_widget.ctl_bar.clear_adhoc_btns()
        fullscreen_btn = video_widget.ctl_bar.add_adhoc_btn('全屏')
        hide_btn = video_widget.ctl_bar.add_adhoc_btn('退出画中画')
        fullscreen_btn.clicked.connect(self.toggle_pip_fullscreen)
        hide_btn.clicked.connect(lambda: self.set_mode(Mode.normal))
        self._pip_container.show()
        self._app.ui.mpv_widget.show()
        self._show_app_other_widgets()
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
        logger.info("exit video-show picture in picture mode")

    def toggle_pip_fullscreen(self):
        self._pip_container.setWindowState(
            self._pip_container.windowState() ^ Qt.WindowFullScreen)

    def play_mv(self):
        song = self._app.player.current_song
        if song is None:
            return

        # The mv button only shows when there is a valid mv object
        mv = self._app.library.song_get_mv(song)
        self._app.playlist.set_current_model(mv)
        self.enter_normal_mode()

    def on_media_changed(self, media):
        if not media:
            self.set_mode(Mode.none)

    def on_video_format_changed(self, _):
        if self._app.player.video_format is None:
            logger.info('Media has no video, mode to none')
            self.set_mode(Mode.none)
        else:
            if self._is_visible_before is True:
                if self._is_normal_mode():
                    self.set_mode(Mode.normal)
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
