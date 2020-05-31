import logging
from enum import IntEnum

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
        """
        self._app = app
        self._ui = ui
        self._pip_container = ResizableFramelessContainer()
        self._mode = Mode.none
        self._mpv_normal = True
        self._count = 0

        self._ui.pc_panel.mv_btn.clicked.connect(self.play_mv)
        self._ui.toggle_video_btn.clicked.connect(lambda: self.set_mode(Mode.normal))
        self._ui.pc_panel.toggle_pip_btn.clicked.connect(lambda: self.set_mode(Mode.pip))

        self.enter_normal_mode()
        self._app.initialized.connect(
            lambda app: self.exit_normal_mode(), weak=False)
        self._app.player.video_format_changed.connect(
            self.on_video_format_changed, aioqueue=True)

        self._pip_container.setMinimumSize(100, 80)
        self._pip_container.hide()

    def show_ctl_btns(self):
        self._ui.toggle_video_btn.show()
        self._ui.pc_panel.toggle_pip_btn.show()

    def hide_ctl_btns(self):
        self._ui.toggle_video_btn.hide()
        self._ui.pc_panel.toggle_pip_btn.hide()

    def enter_normal_mode(self):
        """enter normal mode"""
        self._ui.bottom_panel.hide()
        self._ui._splitter.hide()
        self._ui.pc_panel.toggle_video_btn.setText('▽')
        logger.info("enter video-show normal mode")
        if self._mpv_normal is False:
            self._count += 1
            self._ui.mpv_widget.hide()
            self._pip_container.detach()
            self._app.layout().insertWidget(1, self._ui.mpv_widget)
            self._mpv_normal = True
            self._ui.mpv_widget.show()
            self._replay()
        self._ui.mpv_widget.show()

    def exit_normal_mode(self):
        self._ui.mpv_widget.hide()
        self._ui._splitter.show()
        self._ui.bottom_panel.show()
        self._ui.pc_panel.toggle_video_btn.setText('△')
        logger.info("exit video-show normal mode")

    def enter_pip_mode(self):
        """enter picture in picture mode"""
        # hide toggle_normal_mode button
        # when we exit pip mode, we should show it
        self._ui.toggle_video_btn.hide()
        logger.info("enter video-show picture in picture mode")
        if self._mpv_normal is True:
            self._count += 1
            self._ui.mpv_widget.hide()
            self._app.layout().removeWidget(self._ui.mpv_widget)
            self._pip_container.attach_widget(self._ui.mpv_widget)
            self._mpv_normal = False
            self._pip_container.show()
            self._ui.mpv_widget.show()
            self._replay()
        self._pip_container.show()
        self._ui.mpv_widget.show()

    def exit_pip_mode(self):
        """exit picture in picture mode and enter normal mode"""
        self._pip_container.hide()
        self._ui.mpv_widget.hide()
        self._ui.toggle_video_btn.show()
        logger.info("exit video-show picture in picture mode")

    #
    # signal callbacks
    #

    def play_mv(self):
        song = self._app.player.current_song
        mv = song.mv if song else None
        if mv is not None:
            if mv.meta.support_multi_quality:
                media, _ = mv.select_media()
            else:
                media = mv.media
            self._ui.toggle_video_btn.show()
            self.enter_normal_mode()
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
            if self._count <= 0:
                self.set_mode(Mode.none)
            self._count -= 1
        else:
            self.show_ctl_btns()

    #
    # private methods
    #
    def _replay(self):
        player = self._app.player
        pos = player.position
        media = player.current_media
        player.pause()
        signal_count_down = 2

        def before_media_change(old_media, new_media):
            global signal_count_down
            signal_count_down -= 1
            if old_media is media and signal_count_down <= 0:
                player.media_about_to_changed.disconnect(before_media_change)
                player.set_play_range()
                player.resume()

        player.set_play_range(start=pos)
        player.play(media)
        player.media_about_to_changed.connect(before_media_change,
                                              weak=False)
        player.resume()
