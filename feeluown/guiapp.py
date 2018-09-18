import asyncio
import logging
import os
from contextlib import contextmanager
from functools import partial

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QStyle,
    QWidget,
)

from fuocore.player import State as PlayerState

from feeluown.components.history import HistoriesModel
from feeluown.components.provider import ProvidersModel
from feeluown.components.playlists import PlaylistsModel

from .app import CliApp, App
from .consts import APP_ICON
from .helpers import use_mac_theme
from .hotkey import Hotkey
from .img_ctl import ImgController
from .request import Request
from .tips import TipsManager
from .ui import Ui

logger = logging.getLogger(__name__)


class AppCodeRunnerMixin(object):
    def __init__(self):
        self._g = {}

    def exec_(self, code):
        obj = compile(code, '<string>', 'single')
        self._g.update({
            'app': self,
            'player': self.player
        })
        exec(obj, self._g, self._g)


class GuiApp(CliApp, QWidget, AppCodeRunnerMixin):
    """
    FIXME: Subclass must call initialize to make this mixin
    work properly, which seems to be little bit strange. But
    this mixin helps avoid duplicate code temporarily.
    """

    mode = App.GuiMode | App.CliMode

    def __init__(self, pubsub_gateway, player=None):
        CliApp.__init__(self, pubsub_gateway, player=None)
        QWidget.__init__(self)

        self.request = Request(self)
        self.tips_manager = TipsManager(self)
        self.hotkey_manager = Hotkey(self)
        self.img_ctl = ImgController(self)

        self.playlists = PlaylistsModel(parent=self)
        self.histories = HistoriesModel(parent=self)
        self.providers = ProvidersModel(parent=self)

        self.ui = Ui(self)

        self.player_pixmap = None

        self.resize(1000, 618)
        self.setObjectName('app')
        QApplication.setWindowIcon(QIcon(APP_ICON))

        self.bind_signal()

    def initialize(self):
        super().initialize()
        self.load_qss()
        self.tips_manager.show_random_tip()

    def load_qss(self):
        if not use_mac_theme():
            return
        filepath = os.path.abspath(__file__)
        dirname = os.path.dirname(filepath)
        qssfilepath = os.path.join(dirname, 'mac.qss')
        with open(qssfilepath) as f:
            s = f.read()

            QApplication.instance().setStyleSheet(s)

    def bind_signal(self):
        top_panel = self.ui.top_panel

        self.player.state_changed.connect(self._on_player_status_changed)
        self.player.position_changed.connect(self._on_player_position_changed)
        self.player.duration_changed.connect(self._on_player_duration_changed)
        self.request.connected_signal.connect(self._on_network_connected)
        self.request.disconnected_signal.connect(self._on_network_disconnected)
        self.request.slow_signal.connect(self._on_network_slow)
        self.request.server_error_signal.connect(self._on_network_server_error)
        #top_panel.pc_panel.volume_slider.sliderMoved.connect(
        #    self.change_volume)

    @contextmanager
    def create_action(self, s):
        show_msg = self.ui.magicbox.show_msg

        class Action(object):
            def set_progress(self, value):
                value = int(value * 100)
                show_msg(s + '...{}%'.format(value), timeout=-1)

            def failed(self):
                show_msg(s + '...failed', timeout=-1)

        show_msg(s + '...', timeout=-1)  # doing
        try:
            yield Action()
        except Exception:
            show_msg(s + '...error')  # error
            raise
        else:
            show_msg(s + '...done')  # done

    def _on_player_position_changed(self, ms):
        self.ui.top_panel.pc_panel.on_position_changed(ms*1000)
        self.ui.top_panel.pc_panel.progress_slider.update_state(ms*1000)

    def _on_player_duration_changed(self, ms):
        self.ui.top_panel.pc_panel.on_duration_changed(ms*1000)
        self.ui.top_panel.pc_panel.progress_slider.set_duration(ms*1000)

    def _on_player_status_changed(self, state):
        pp_btn = self.ui.top_panel.pc_panel.pp_btn
        if use_mac_theme():
            return
        if state == PlayerState.playing:
            pp_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            pp_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def _on_network_slow(self):
        pass

    def _on_network_connected(self):
        pass

    def _on_network_server_error(self):
        pass

    def _on_network_disconnected(self):
        pass

    def change_volume(self, value):
        self.player.volume = value

    def pixmap_from_url(self, url, callback=None):
        # FIXME: only neteasemusic img url accept the params
        data = {'param': '{0}y{0}'.format(self.width())}
        res = self.request.get(url, data)
        if res is None:
            return None
        img = QImage()
        img.loadFromData(res.content)
        pixmap = QPixmap(img)
        if pixmap.isNull():
            return None
        if callback is not None:
            callback(pixmap)
        return pixmap

    def closeEvent(self, event):
        try:
            self.player.stop()
            self.player.shutdown()
        except Exception as e:
            pass
        QApplication.quit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
