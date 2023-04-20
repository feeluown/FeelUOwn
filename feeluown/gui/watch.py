import logging
from contextlib import contextmanager
from enum import IntEnum

from PyQt5.QtCore import Qt

from feeluown.player.mpvplayer import _mpv_set_property_string
from feeluown.gui.widgets.frameless import ResizableFramelessContainer

logger = logging.getLogger(__name__)


class Mode(IntEnum):
    none = 0    # Hide all video related widgets, including controller buttons.
    normal = 1  # Show video widget inside the main window.
    pip = 2     # Show video widget in a detached container (picture in picture).


class WatchManager:
    def __init__(self, app):
        """video view controller

        :type app: feeluown.app.App
        :type ui: feeluown.ui.Ui
        """
        self._app = app
        self._pip_container = ResizableFramelessContainer()

        self._mode = Mode.none
        # Otherwise, the parent of mpv widget is pip container.
        self._parent_is_normal = True
        self._parent_is_changing = False
        #: Is the video widget visible before.
        self._is_visible_before = False

    def initialize(self):
        self._initialize_mpv_video_renderring()

        self._ui = self._app.ui
        self._ui.pc_panel.mv_btn.clicked.connect(self.play_mv)
        self._ui.pc_panel.toggle_video_btn.clicked.connect(lambda: self.set_mode(Mode.normal))  # noqa
        self._ui.pc_panel.toggle_pip_btn.clicked.connect(lambda: self.set_mode(Mode.pip))
        self._app.player.media_changed.connect(self.on_media_changed, aioqueue=True)
        self._app.player.video_format_changed.connect(self.on_video_format_changed, aioqueue=True)  # noqa

        self._pip_container.setMinimumSize(200, 130)
        self._pip_container.hide()
        self._ui.pc_panel.toggle_video_btn.hide()
        self._ui.pc_panel.toggle_pip_btn.hide()

    def show_ctl_btns(self):
        self._app.ui.pc_panel.toggle_video_btn.show()
        self._app.ui.pc_panel.toggle_pip_btn.show()

    def hide_ctl_btns(self):
        self._app.ui.pc_panel.toggle_video_btn.hide()
        self._app.ui.pc_panel.toggle_pip_btn.hide()

    @contextmanager
    def change_parent(self):
        self._parent_is_changing = True
        self._before_change_mpv_widget_parent()
        yield
        self._after_change_mpv_widget_parent()
        self._parent_is_changing = False

    def enter_normal_mode(self):
        """enter normal mode"""
        self._app.ui.bottom_panel.hide()
        self._app.ui._splitter.hide()
        self._app.ui.pc_panel.toggle_video_btn.show()
        self._app.ui.pc_panel.toggle_video_btn.setText('▽')
        logger.info("enter video-show normal mode")
        self._app.ui.mpv_widget.overlay_auto_visible = False
        self._app.ui.mpv_widget.keep_wh_ratio = False
        if self._parent_is_normal is False:
            with self.change_parent():
                self._app.ui.mpv_widget.hide()
                self._app.ui.mpv_widget.shutdown()
                self._pip_container.detach()
                self._app.layout().insertWidget(1, self._app.ui.mpv_widget)
                self._parent_is_normal = True
                self._app.ui.mpv_widget.show()
        else:
            self._app.ui.mpv_widget.show()

    def exit_normal_mode(self):
        self._app.ui.mpv_widget.hide()
        self._app.ui._splitter.show()
        self._app.ui.bottom_panel.show()
        self._app.ui.pc_panel.toggle_video_btn.setText('△')
        logger.info("exit video-show normal mode")

    def enter_pip_mode(self):
        """enter picture in picture mode"""
        logger.info("enter video-show picture in picture mode")
        self._app.ui.mpv_widget.overlay_auto_visible = True
        if self._parent_is_normal is True:
            width = self._app.player._mpv.width
            height = self._app.player._mpv.height
            with self.change_parent():
                self._app.ui.mpv_widget.hide()
                self._app.ui.mpv_widget.shutdown()
                self._app.ui._splitter.show()
                self._app.ui.bottom_panel.show()
                self._app.layout().removeWidget(self._app.ui.mpv_widget)
                self._pip_container.attach_widget(self._app.ui.mpv_widget)
                self._parent_is_normal = False
                self._pip_container.show()
                self._app.ui.mpv_widget.show()
            proper_width = max(min(width, 640), 320)
            proper_height = height * proper_width // width
            self._pip_container.resize(proper_width, proper_height)
        else:
            self._pip_container.show()
            self._app.ui.mpv_widget.show()

    def exit_pip_mode(self):
        """exit picture in picture mode"""
        self._pip_container.hide()
        self._app.ui.mpv_widget.hide()
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

    def set_mode(self, mode):
        self._is_visible_before = self._app.ui.mpv_widget.isVisible()

        # So that user can call set_mode(0/1/2) in REPL.
        mode = Mode(mode)
        # change mode to none, exit orignal mode
        if mode is Mode.none:
            if self._mode is Mode.normal:
                self.exit_normal_mode()
            elif self._mode is Mode.pip:
                self.exit_pip_mode()
            self._mode = mode
            self.hide_ctl_btns()
            return
        # change current mode to mode
        #
        # if mode is same as the current mode, exit mode
        # if mode is not same as the current mode, exit
        # current mode and enter mode
        if self._mode is Mode.none:
            if mode is Mode.normal:
                self.enter_normal_mode()
            else:
                self.enter_pip_mode()
            self._mode = mode
        elif self._mode is Mode.normal:
            self.exit_normal_mode()
            self._mode = Mode.none
            if mode is Mode.pip:
                self.enter_pip_mode()
                self._mode = mode
        else:
            self.exit_pip_mode()
            self._mode = Mode.none
            if mode is Mode.normal:
                self.enter_normal_mode()
                self._mode = mode

    def on_media_changed(self, media):
        if not media:
            logger.info('No media is played, set mode to none')
            self.set_mode(Mode.none)

    def on_video_format_changed(self, video_format):
        if self._app.player.video_format is None:
            # Ignore the signal if parent is changing to prevent unexpected problem.
            if self._parent_is_changing:
                return
            logger.info('Media has no video, mode to none')
            self.set_mode(Mode.none)
        else:
            self.show_ctl_btns()
            if self._is_visible_before is True:
                mode = Mode.normal if self._parent_is_normal is True else Mode.pip
                self.set_mode(mode)

    #
    # private methods
    #
    def _initialize_mpv_video_renderring(self):
        # HACK: Show mpv_widget once to initialize mpv video renderring correctly.
        # Remember to set aioqueue to true so that mpv_widget is hidden after the
        # app(Qt) event loop is started.
        self._app.ui.mpv_widget.show()
        self._app.started.connect(lambda *_: self._app.ui.mpv_widget.hide(), weak=False)

    def _before_change_mpv_widget_parent(self):
        """
        According to Qt docs, reparenting an OpenGLWidget will destory the GL context.
        In mpv widget, it calls _mpv_opengl_cb_uninit_gl. After uninit_gl, mpv can't show
        video anymore because video_out is destroyed.

        See mpv mpv_opengl_cb_uninit_gl implementation for more details.
        """
        _mpv_set_property_string(self._app.player._mpv.handle, b'vid', b'no')

    def _after_change_mpv_widget_parent(self):
        """
        To recover the video show, we should reinit gl and reinit video. gl is
        automatically reinited when the mpv_widget do painting. We should
        manually reinit video.

        NOTE(cosven): After some investigation, I found that the API in mpv to
        reinit video_out(maybe video is almost same as video_out)
        is init_best_video_out. Theoretically, sending 'video-reload' command
        will trigger this API. However, we can't run this command
        in our case and I don't know why. Another way to trigger
        the API is to switch track. Changing vid property just switch the track.

        Inpect mpv init_best_video_out caller for more details. You should see
        mp_switch_track_n is one of the entrypoint.
        """
        _mpv_set_property_string(self._app.player._mpv.handle, b'vid', b'1')
