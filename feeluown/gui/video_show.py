import logging
from contextlib import contextmanager
from enum import IntEnum

from feeluown.player.mpvplayer import _mpv_set_property_string

from feeluown.gui.widgets.frameless import ResizableFramelessContainer

logger = logging.getLogger(__name__)


class Mode(IntEnum):
    none = 0
    normal = 1
    pip = 2


class VideoShowCtl:
    def __init__(self, app, ui):
        """video show controller

        :type app: feeluown.app.App
        :type ui: feeluown.ui.Ui
        """
        self._app = app
        self._ui = ui
        self._pip_container = ResizableFramelessContainer()
        self._mode = Mode.none
        self._parent_is_normal = True
        self._parent_is_changing = False

        self._ui.pc_panel.mv_btn.clicked.connect(self.play_mv)
        self._ui.toggle_video_btn.clicked.connect(lambda: self.set_mode(Mode.normal))
        self._ui.pc_panel.toggle_pip_btn.clicked.connect(lambda: self.set_mode(Mode.pip))

        self._ui.mpv_widget.show()
        self._app.initialized.connect(
            lambda app: self._ui.mpv_widget.hide(), weak=False)
        self._app.player.video_format_changed.connect(
            self.on_video_format_changed, aioqueue=True)

        self._pip_container.setMinimumSize(200, 130)
        self._pip_container.hide()

    def show_ctl_btns(self):
        self._ui.toggle_video_btn.show()
        self._ui.pc_panel.toggle_pip_btn.show()

    def hide_ctl_btns(self):
        self._ui.toggle_video_btn.hide()
        self._ui.pc_panel.toggle_pip_btn.hide()

    @contextmanager
    def change_parent(self):
        self._parent_is_changing = True
        self._before_change_mpv_widget_parent()
        yield
        self._after_change_mpv_widget_parent()
        self._parent_is_changing = False

    def enter_normal_mode(self):
        """enter normal mode"""
        self._ui.bottom_panel.hide()
        self._ui._splitter.hide()
        self._ui.pc_panel.toggle_video_btn.show()
        self._ui.pc_panel.toggle_video_btn.setText('▽')
        logger.info("enter video-show normal mode")
        if self._parent_is_normal is False:
            with self.change_parent():
                self._ui.mpv_widget.hide()
                self._pip_container.detach()
                self._app.layout().insertWidget(1, self._ui.mpv_widget)
                self._parent_is_normal = True
                self._ui.mpv_widget.show()
        else:
            self._ui.mpv_widget.show()

    def exit_normal_mode(self):
        self._ui.mpv_widget.hide()
        self._ui._splitter.show()
        self._ui.bottom_panel.show()
        self._ui.pc_panel.toggle_video_btn.setText('△')
        logger.info("exit video-show normal mode")

    def enter_pip_mode(self):
        """enter picture in picture mode"""
        self._ui.toggle_video_btn.hide()
        logger.info("enter video-show picture in picture mode")
        if self._parent_is_normal is True:
            width = self._app.player._mpv.width
            height = self._app.player._mpv.height
            with self.change_parent():
                self._ui.mpv_widget.hide()
                self._ui._splitter.show()
                self._ui.bottom_panel.show()
                self._app.layout().removeWidget(self._ui.mpv_widget)
                self._pip_container.attach_widget(self._ui.mpv_widget)
                self._parent_is_normal = False
                self._pip_container.show()
                self._ui.mpv_widget.show()
            proper_width = min(width, 666)
            proper_height = height * proper_width / width
            self._ui.mpv_widget.resize(proper_width, proper_height)
        else:
            self._pip_container.show()
            self._ui.mpv_widget.show()

    def exit_pip_mode(self):
        """exit picture in picture mode"""
        self._pip_container.hide()
        self._ui.mpv_widget.hide()
        logger.info("exit video-show picture in picture mode")

    #
    # signal callbacks
    #

    def play_mv(self):
        song = self._app.player.current_song
        song = self._app.library.cast_model_to_v1(song)
        mv = song.mv if song else None
        if mv is not None:
            if mv.meta.support_multi_quality:
                media, _ = mv.select_media()
            else:
                media = mv.media
            self.set_mode(Mode.normal)
            self._app.player.play(media)

    def set_mode(self, mode):
        # change mode to none, exit orignal mode
        logger.info(f"set video show mode to {mode}")
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

    def on_video_format_changed(self, video_format):
        """
        When video is available, show control buttons. If video
        is unavailable, hide video and control buttons.
        """
        logger.info(f"video format changed to {video_format}")
        if video_format is None:
            # ignore the signal if parent is changing
            if self._parent_is_changing:
                return
            self.set_mode(Mode.none)
        else:
            self.show_ctl_btns()

    #
    # private methods
    #
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
