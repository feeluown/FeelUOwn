import os
import sys

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
from feeluown.gui.provider_ui import ProviderUiManager, CurrentProviderUiManager
from feeluown.gui.uimodels.playlist import PlaylistUiManager
from feeluown.gui.uimodels.my_music import MyMusicUiManager

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

        # Note that QApplication.setFont only works for those widgets that created
        # after `QApplication.exec` (tested on macOS).
        if sys.platform == 'win32':
            font = QApplication.font()
            # By default, it uses SimSun(宋体) on windows, which is a little ugly.
            # "Segoe UI Symbol" is used to render charactor symbols.
            # "Microsoft Yahei" is used to render chinese (and english).
            # Choose a default sans-serif font when the first two fonts do not work,
            font.setFamilies(['Segoe UI Symbol', 'Microsoft YaHei', 'sans-serif'])

            # When a HiDPI screen is used, users need to set both font DPI and
            # screen scale factor to make it working properly when pointSize is used.
            # It's hard for most users to set them right.
            # When using pixelSize, users only need to set screen scale factor.
            # In other words, only QT_AUTO_SCREEN_SCALE_FACTOR=1 is needed to set
            # and feeluown can works properly in HiDPI environment.
            #
            # Based on past experience, 13px is the default font size for all platform,
            # including windows, linux and macOS.
            font.setPixelSize(13)
            QApplication.setFont(font)
        elif sys.platform == 'darwin':
            font = QApplication.font()
            # The default font can not show chinese in bold.
            font.setFamilies(['arial', 'Hiragino Sans GB', 'sans-serif'])
            QApplication.setFont(font)

        QWidget.__init__(self)
        App.__init__(self, *args, **kwargs)

        GuiApp.__q_app = QApplication.instance()

        self.setObjectName('app')

        # GUI 的一些辅助管理模块
        self.theme_mgr = ThemeManager(self, parent=self)
        self.tips_mgr = TipsManager(self)
        self.hotkey_mgr = HotkeyManager(self)
        self.img_mgr = ImgManager(self)
        self.watch_mgr = WatchManager(self)

        # GUI 组件的数据管理模块
        self.pvd_ui_mgr = self.pvd_uimgr = ProviderUiManager(self)
        self.current_pvd_ui_mgr = CurrentProviderUiManager(self)
        self.pl_uimgr = PlaylistUiManager(self)
        self.mymusic_uimgr = MyMusicUiManager(self)

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
        self.watch_mgr.initialize()
        self.browser.initialize()
        QApplication.instance().aboutToQuit.connect(self.about_to_exit)

    def run(self):
        self.show()
        super().run()

    def apply_state(self, state):
        super().apply_state(state)
        coll_library = self.coll_mgr.get_coll_library()
        self.browser.goto(page=f'/colls/{coll_library.identifier}')

        gui = state.get('gui', {})
        lyric = gui.get('lyric', {})
        local_storage = gui.get('browser', {}).get('local_storage', {})
        self.browser.local_storage = local_storage
        self.ui.lyric_window.apply_state(lyric)

    def dump_state(self):
        state = super().dump_state()
        state['gui'] = {
            'lyric': self.ui.lyric_window.dump_state(),
            'browser': {
                'local_storage': self.browser.local_storage
            }
        }
        return state

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
