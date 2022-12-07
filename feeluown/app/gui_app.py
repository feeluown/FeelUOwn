import os

from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt5.QtWidgets import QApplication, QWidget

from feeluown.gui.browser import Browser
from feeluown.gui.hotkey import HotkeyManager
from feeluown.gui.image import ImgManager
from feeluown.gui.theme import ThemeManager
from feeluown.gui.tips import TipsManager
from feeluown.gui.watch import WatchManager
from feeluown.gui.ui import Ui
from feeluown.gui.tray import Tray
from feeluown.gui.uimodels.provider import ProviderUiManager
from feeluown.gui.uimodels.playlist import PlaylistUiManager
from feeluown.gui.uimodels.my_music import MyMusicUiManager
from feeluown.gui.uimodels.collection import CollectionUiManager

from feeluown.collection import CollectionManager

from .app import App


class GuiApp(App, QWidget):
    def __init__(self, *args, **kwargs):
        config = args[1]
        pkg_root_dir = os.path.join(os.path.dirname(__file__), '..')
        icons_dir = os.path.join(pkg_root_dir, 'gui/assets/icons')
        QDir.addSearchPath('icons', icons_dir)
        QGuiApplication.setWindowIcon(QIcon(QPixmap('icons:feeluown.png')))
        # Set desktopFileName so that the window icon is properly shown under wayland.
        # I don't know if this setting brings other benefits or not.
        # https://github.com/pyfa-org/Pyfa/issues/1607#issuecomment-392099878
        QApplication.setDesktopFileName('FeelUOwn')
        QApplication.instance().setQuitOnLastWindowClosed(not config.ENABLE_TRAY)
        QApplication.instance().setApplicationName('FeelUOwn')

        QWidget.__init__(self)
        App.__init__(self, *args, **kwargs)

        GuiApp.__q_app = QApplication.instance()

        self.setObjectName('app')

        # GUI 的一些辅助管理模块
        self.coll_mgr = CollectionManager(self)
        self.theme_mgr = ThemeManager(self)
        self.tips_mgr = TipsManager(self)
        self.hotkey_mgr = HotkeyManager(self)
        self.img_mgr = ImgManager(self)
        self.watch_mgr = WatchManager(self)

        # GUI 组件的数据管理模块
        self.pvd_uimgr = ProviderUiManager(self)
        self.pl_uimgr = PlaylistUiManager(self)
        self.mymusic_uimgr = MyMusicUiManager(self)
        self.coll_uimgr = CollectionUiManager(self)

        self.browser = Browser(self)
        self.ui = Ui(self)
        if self.config.ENABLE_TRAY:
            self.tray = Tray(self)
        self.show_msg = self.ui._message_line.show_msg

    def initialize(self):
        super().initialize()

        self.hotkey_mgr.initialize()
        self.theme_mgr.initialize()
        if self.config.ENABLE_TRAY:
            self.tray.initialize()
            self.tray.show()
        self.tips_mgr.show_random_tip()
        self.coll_uimgr.initialize()
        self.watch_mgr.initialize()
        self.browser.initialize()
        QApplication.instance().aboutToQuit.connect(self.about_to_exit)

    def run(self):
        super().run()
        self.show()

    def load_state(self):
        super().load_state()
        coll_library = self.coll_uimgr.get_coll_library()
        coll_id = self.coll_uimgr.get_coll_id(coll_library)
        self.browser.goto(page=f'/colls/{coll_id}')

    def closeEvent(self, _):
        if not self.config.ENABLE_TRAY:
            self.exit()

    def mouseReleaseEvent(self, e):
        if not self.rect().contains(e.pos()):
            return
        if e.button() == Qt.BackButton:
            self.browser.back()
        elif e.button() == Qt.ForwardButton:
            self.browser.forward()

    def exit_player(self):
        # Destroy GL context or mpv renderer
        self.ui.mpv_widget.shutdown()
        super().exit_player()

    def about_to_exit(self):
        super().about_to_exit()
        QApplication.instance().aboutToQuit.disconnect(self.about_to_exit)

    def exit(self):
        QApplication.exit()
