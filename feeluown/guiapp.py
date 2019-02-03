import logging
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget

from feeluown.components.history import HistoriesModel
from feeluown.components.provider import ProvidersModel
from feeluown.components.playlists import PlaylistsModel
from feeluown.components.my_music import MyMusicModel
from feeluown.components.collections import CollectionsModel
from feeluown.protocol.collection import CollectionManager

from .app import App
from .browser import Browser
from .consts import APP_ICON
from .helpers import use_mac_theme
from .hotkey import Hotkey
from .img_ctl import ImgController
from .tips import TipsManager
from .ui import Ui

logger = logging.getLogger(__name__)


class GuiApp(QWidget, App):
    mode = App.GuiMode | App.CliMode

    def __init__(self, player_kwargs=None):
        QWidget.__init__(self)
        App.__init__(self, player_kwargs=player_kwargs)

        self.coll_mgr = CollectionManager(self)
        self.tips_mgr = TipsManager(self)
        self.hotkey_mgr = Hotkey(self)
        self.img_ctl = ImgController(self)

        # alpha
        self.playlists = PlaylistsModel(parent=self)
        self.histories = HistoriesModel(parent=self)
        self.providers = ProvidersModel(parent=self)
        self.my_music = MyMusicModel(parent=self)
        self.collections = CollectionsModel(parent=self)

        self.browser = Browser(self)  # 在 ui 初始化之前初始化
        self.ui = Ui(self)
        self.show_msg = self.ui.magicbox.show_msg
        self.resize(1000, 618)
        self.setObjectName('app')
        QApplication.setWindowIcon(QIcon(APP_ICON))

    def initialize(self):
        super().initialize()
        self.load_qss()
        self.tips_mgr.show_random_tip()
        self.coll_mgr.scan()

    def load_qss(self):
        if not use_mac_theme():
            return
        filepath = os.path.abspath(__file__)
        dirname = os.path.dirname(filepath)
        qssfilepath = os.path.join(dirname, 'light.qss')
        with open(qssfilepath) as f:
            s = f.read()
            QApplication.instance().setStyleSheet(s)

    def closeEvent(self, _):
        try:
            self.shutdown()
        finally:
            QApplication.quit()
