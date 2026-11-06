import os
import sys
import logging

from PyQt6.QtCore import Qt, QDir, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget

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


logger = logging.getLogger(__name__)


class GuiApp(App, QWidget):

    def __init__(self, *args, **kwargs):
        config = args[1]
        pkg_root_dir = os.path.join(os.path.dirname(__file__), '..')
        icons_dir = os.path.join(pkg_root_dir, 'gui/assets/icons')
        QDir.addSearchPath('icons', icons_dir)
        # Tested on macOS and Arch Linux
        # macOS: must initialize QApplication before constructing a pixmap object.
        # Arch Linux: it may core if QApplication is initialized here.
        if sys.platform == 'darwin':
            qapp = QApplication.instance()
            if qapp is None:
                qapp = QApplication(['FeelUOwn'])
            GuiApp.__q_app = qapp
        # Set desktopFileName so that the window icon is properly shown under wayland.
        # I don't know if this setting brings other benefits or not.
        # https://github.com/pyfa-org/Pyfa/issues/1607#issuecomment-392099878
        QApplication.setDesktopFileName('FeelUOwn')
        QApplication.instance().setQuitOnLastWindowClosed(not config.ENABLE_TRAY)
        QApplication.instance().setApplicationName('FeelUOwn')
        QGuiApplication.setWindowIcon(QIcon(QPixmap('icons:feeluown.png')))

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

        # auxiliary management modules for the GUI
        self.theme_mgr = ThemeManager(self, parent=self)
        self.tips_mgr = TipsManager(self)
        self.hotkey_mgr = HotkeyManager(self)
        self.img_mgr = ImgManager(self)
        self.watch_mgr = WatchManager(self)

        # data management modules for GUI components
        self.pvd_ui_mgr = self.pvd_uimgr = ProviderUiManager(self)
        self.current_pvd_ui_mgr = CurrentProviderUiManager(self)
        self.pl_uimgr = PlaylistUiManager(self)
        self.mymusic_uimgr = MyMusicUiManager(self)

        self.browser = Browser(self)
        self.ui = Ui(self)
        if self.config.ENABLE_TRAY:
            self.tray = Tray(self)
        self.show_msg = self.ui._message_line.show_msg
        # Set in apply_state(); run() navigates to homepage if pending.
        # _pending_homepage means navigation is needed; _homepage_scheduled
        # means a QTimer callback is already queued. _pending_homepage is
        # cleared only when navigation actually runs; _homepage_scheduled is
        # cleared when the queued callback fires (or when run() resets a
        # stale marker to retry a dropped schedule).
        self._pending_homepage = False
        self._homepage_scheduled = False

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
        # Homepage navigation (and its data fetch) is deferred until after
        # the window is shown so first paint is not blocked. apply_state()
        # sets _pending_homepage.
        if self._pending_homepage:
            # A previously queued singleShot may have been dropped (event
            # loop never pumped since scheduling). Reset the stale marker so
            # this run() retries instead of early-returning forever. In the
            # worst case both the dropped and the new timer fire, and the
            # duplicate goto is harmless (history guard skips same-page push).
            self._homepage_scheduled = False
            self._goto_homepage_async()

    def _goto_homepage_async(self):
        # Dedupe: a queued navigation stays queued; callers check
        # _homepage_scheduled via run()/apply_state().
        if self._homepage_scheduled:
            return
        if not self._pending_homepage:
            return
        # Headless/test flows without a running event loop would queue a
        # QTimer.singleShot that never fires. Navigate synchronously there
        # so current_page is set deterministically (old behavior).
        if not self._event_loop_running():
            self._goto_homepage_sync()
            return
        self._homepage_scheduled = True

        def _goto():
            self._homepage_scheduled = False
            self._goto_homepage_sync()
        # NOTE: QTimer.singleShot() does not raise when no loop is running;
        # it silently never fires. The _event_loop_running() check above is
        # the real headless fallback, not this try/except (kept for safety).
        try:
            QTimer.singleShot(0, _goto)
        except Exception:  # noqa
            self._homepage_scheduled = False
            self._goto_homepage_sync()

    def _goto_homepage_sync(self):
        self._pending_homepage = False
        try:
            self.browser.goto(page='/homepage')
        except Exception as e:  # noqa
            # NOTE: this only catches synchronous navigation errors (bad
            # route, lazy page import failure). Homepage data-fetch failures
            # happen later inside the async render coroutine scheduled by
            # Browser._goto and surface as task exceptions, not here.
            logger.exception('Deferred goto homepage failed')
            try:
                self.show_msg(f'Load homepage failed: {e}')
            except Exception:  # noqa
                pass

    @staticmethod
    def _event_loop_running():
        import asyncio

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return False
        return True

    def apply_state(self, state):
        super().apply_state(state)
        # Browser state that does not need network is restored here.
        gui = state.get('gui', {})
        lyric = gui.get('lyric', {})
        local_storage = gui.get('browser', {}).get('local_storage', {})
        self.browser.local_storage = local_storage
        self.ui.lyric_window.apply_state(lyric)
        # Defer homepage navigation to run() so window shows faster. Note the
        # state-restore order change vs. old code (which navigated first):
        # local_storage/lyric are restored here before the deferred
        # navigation runs, so homepage now sees restored local_storage.
        # If the window is already visible (e.g. apply_state called after
        # run in tests or future state-restore flows), schedule navigation
        # now instead of leaving a stale pending flag. Double apply_state()
        # collapses via the _homepage_scheduled guard in _goto_homepage_async.
        if self.isVisible():
            if not self._pending_homepage:
                self._pending_homepage = True
            self._goto_homepage_async()
        else:
            self._pending_homepage = True

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
        if not self.rect().contains(e.position().toPoint()):
            return
        if e.button() == Qt.MouseButton.BackButton:
            self.browser.back()
        elif e.button() == Qt.MouseButton.ForwardButton:
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
