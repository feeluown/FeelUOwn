import asyncio
import logging
import json
import os
import sys
from functools import partial
from contextlib import contextmanager

from feeluown.library import Library
from feeluown.utils.dispatch import Signal
from feeluown.models import Resolver, reverse, resolve, \
    ResolverNotFound
from feeluown.player import PlaybackMode, Playlist

from feeluown.lyric import LiveLyric
from feeluown.pubsub import (
    Gateway as PubsubGateway,
    HandlerV1 as PubsubHandlerV1,
    LiveLyricPublisher
)

from feeluown.utils.request import Request
from feeluown.utils.utils import is_port_inuse
from feeluown.rpc.server import FuoServer
from .consts import STATE_FILE
from .player import FM, Player
from .plugin import PluginsManager
from .version import VersionManager
from .task import TaskManager

logger = logging.getLogger(__name__)


class App:
    """App 基类"""

    DaemonMode = 0x0001  # 开启 daemon
    GuiMode = 0x0010     # 显示 GUI
    CliMode = 0x0100     # 命令行模式

    def __init__(self, config):
        self.mode = config.MODE  # DEPRECATED: use app.config.MODE instead
        self.config = config
        self.initialized = Signal()
        self.about_to_shutdown = Signal()

        # For code auto completion
        self.library: Library = None
        self.playlist: Playlist = None
        self.player: Player = None

        self.about_to_shutdown.connect(lambda _: self.dump_state(), weak=False)

    def show_msg(self, msg, *args, **kwargs):
        """在程序中显示消息，一般是用来显示程序当前状态"""
        # pylint: disable=no-self-use, unused-argument
        logger.info(msg)

    def get_listen_addr(self):
        return '0.0.0.0' if self.config.ALLOW_LAN_CONNECT else '127.0.0.1'

    def load_state(self):
        playlist = self.playlist
        player = self.player

        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            logger.exception('invalid state file')
        else:
            player.volume = state['volume']
            playlist.playback_mode = PlaybackMode(state['playback_mode'])
            songs = []
            for song in state['playlist']:
                try:
                    song = resolve(song)
                except ResolverNotFound:
                    pass
                else:
                    songs.append(song)
            playlist.set_models(songs)
            if songs and self.mode & App.GuiMode:
                self.browser.goto(page='/player_playlist')

            song = state['song']

            def before_media_change(old_media, media):
                # When the song has no media or preparing media is failed,
                # the current_song is not the song we set.
                #
                # When user play a new media directly through player.play interface,
                # the old media is not None.
                if old_media is not None or playlist.current_song != song:
                    player.media_about_to_changed.disconnect(before_media_change)
                    player.set_play_range()

            if song is not None:
                try:
                    song = resolve(state['song'])
                except ResolverNotFound:
                    pass
                else:
                    player.media_about_to_changed.connect(before_media_change,
                                                          weak=False)
                    player.pause()
                    player.set_play_range(start=state['position'])
                    playlist.set_current_song(song)

    def dump_state(self):
        logger.info("Dump app state")
        playlist = self.playlist
        player = self.player

        song = self.player.current_song
        if song is not None:
            song = reverse(song, as_line=True)
        # TODO: dump player.media
        state = {
            'playback_mode': playlist.playback_mode.value,
            'volume': player.volume,
            'state': player.state.value,
            'song': song,
            'position': player.position,
            'playlist': [reverse(song, as_line=True) for song in playlist.list()],
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)

    @contextmanager
    def create_action(self, s):  # pylint: disable=no-self-use
        """根据操作描述生成 Action (alpha)

        设计缘由：用户需要知道目前程序正在进行什么操作，进度怎么样，
        结果是失败或者成功。这里将操作封装成 Action。
        """
        show_msg = self.show_msg

        class ActionError(Exception):
            pass

        class Action:
            def set_progress(self, value):
                value = int(value * 100)
                show_msg(s + '...{}%'.format(value), timeout=-1)

            def failed(self, msg=''):
                raise ActionError(msg)

        show_msg(s + '...', timeout=-1)  # doing
        try:
            yield Action()
        except ActionError as e:
            show_msg(s + '...failed\t{}'.format(str(e)))
        except Exception as e:
            show_msg(s + '...error\t{}'.format(str(e)))  # error
            raise
        else:
            show_msg(s + '...done')  # done

    def about_to_exit(self):
        logger.info('Do graceful shutdown')
        try:
            self.about_to_shutdown.emit(self)
            self.player.stop()
            self.exit_player()
            # Teardown aio support at the very end.
            Signal.teardown_aio_support()
        except:  # noqa
            logger.exception("about-to-exit failed")
        logger.info('Ready for shutdown')

    def exit_player(self):
        self.player.shutdown()  # this cause 'abort trap' on macOS

    def exit(self):
        self.about_to_exit()


def attach_attrs(app):
    """初始化 app 属性"""
    app.task_mgr = TaskManager(app)
    app.library = Library(app.config.PROVIDERS_STANDBY)
    app.live_lyric = LiveLyric(app)
    player_kwargs = dict(
        audio_device=bytes(app.config.MPV_AUDIO_DEVICE, 'utf-8')
    )
    app.player = Player(**(player_kwargs or {}))
    app.playlist = Playlist(
        app, audio_select_policy=app.config.AUDIO_SELECT_POLICY)
    app.player.set_playlist(app.playlist)
    app.plugin_mgr = PluginsManager(app)
    app.request = Request()
    app.fm = FM(app)

    if app.mode & (app.DaemonMode | app.GuiMode):
        app.version_mgr = VersionManager(app)

    if app.mode & app.DaemonMode:
        app.server = FuoServer(app)
        app.pubsub_gateway = PubsubGateway()
        app._ll_publisher = LiveLyricPublisher(app.pubsub_gateway)

    if app.mode & app.GuiMode:
        from feeluown.uimodels.provider import ProviderUiManager
        from feeluown.uimodels.playlist import PlaylistUiManager
        from feeluown.uimodels.my_music import MyMusicUiManager
        from feeluown.uimodels.collection import CollectionUiManager
        from feeluown.collection import CollectionManager

        from .gui.browser import Browser
        from .gui.hotkey import HotkeyManager
        from .gui.image import ImgManager
        from .gui.theme import ThemeManager
        from .gui.tips import TipsManager
        from .gui.ui import Ui
        from .gui.tray import Tray

        # GUI 的一些辅助管理模块
        app.coll_mgr = CollectionManager(app)
        app.theme_mgr = ThemeManager(app)
        app.tips_mgr = TipsManager(app)
        app.hotkey_mgr = HotkeyManager(app)
        app.img_mgr = ImgManager(app)

        # GUI 组件的数据管理模块
        app.pvd_uimgr = ProviderUiManager(app)
        app.pl_uimgr = PlaylistUiManager(app)
        app.mymusic_uimgr = MyMusicUiManager(app)
        app.coll_uimgr = CollectionUiManager(app)

        app.browser = Browser(app)
        app.ui = Ui(app)
        if app.config.ENABLE_TRAY:
            app.tray = Tray(app)
        #app.show_msg = app.ui.toolbar.status_line.get_item('notify').widget.show_msg


def create_app(config):
    mode = config.MODE

    if mode & App.GuiMode:

        from PyQt5.QtCore import Qt, QDir
        from PyQt5.QtGui import QIcon, QPixmap, QGuiApplication
        from PyQt5.QtWidgets import QApplication, QWidget

        try:
            # HELP: QtWebEngineWidgets must be imported before a
            # QCoreApplication instance is created
            # TODO: add a command line option to control this import
            import PyQt5.QtWebEngineWidgets  # noqa
        except ImportError:
            logger.info('import QtWebEngineWidgets failed')

        from feeluown.utils.compat import DefaultQEventLoopPolicy

        pkg_root_dir = os.path.dirname(__file__)
        icons_dir = os.path.join(pkg_root_dir, 'icons')

        q_app = QApplication(sys.argv)
        QDir.addSearchPath('icons', icons_dir)

        q_app.setQuitOnLastWindowClosed(not config.ENABLE_TRAY)
        q_app.setApplicationName('FeelUOwn')
        QApplication.setWindowIcon(QIcon(QPixmap('icons:feeluown.png')))
        # Set desktopFileName so that the window icon is properly shown under wayland.
        # I don't know if this setting brings other benefits or not.
        # https://github.com/pyfa-org/Pyfa/issues/1607#issuecomment-392099878
        QGuiApplication.setDesktopFileName('FeelUOwn')
        asyncio.set_event_loop_policy(DefaultQEventLoopPolicy())

        class GuiApp(QWidget):
            mode = App.GuiMode

            def __init__(self):
                super().__init__()
                self.setObjectName('app')

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

        class FApp(App, GuiApp):
            def __init__(self, config):
                App.__init__(self, config)
                GuiApp.__init__(self)

            def exit_player(self):
                # Destroy GL context or mpv renderer
                self.ui.mpv_widget.shutdown()
                super().exit_player()

            def exit(self):
                QApplication.exit()

    else:
        FApp = App

    app = FApp(config)
    attach_attrs(app)

    if mode & App.GuiMode:
        q_app.aboutToQuit.connect(app.about_to_exit)

    Resolver.library = app.library
    return app


def init_app(app):
    app.player.position_changed.connect(app.live_lyric.on_position_changed)
    app.playlist.song_changed.connect(app.live_lyric.on_song_changed, aioqueue=True)
    if app.mode & app.DaemonMode:
        app.live_lyric.sentence_changed.connect(app._ll_publisher.publish)

    app.task_mgr.initialize()
    app.plugin_mgr.scan()
    if app.mode & App.GuiMode:
        app.show()
        app.hotkey_mgr.initialize()
        app.theme_mgr.initialize()
        if app.config.ENABLE_TRAY:
            app.tray.initialize()
            app.tray.show()
        app.tips_mgr.show_random_tip()
        app.coll_uimgr.initialize()
        app.browser.initialize()


async def forevermain(app):
    need_window = app.mode & App.GuiMode
    need_server = app.mode & App.DaemonMode

    # Check if there will be any errors that cause start failure.
    # If there is an error, err_msg will not be empty.
    err_msg = ''

    # Check if ports are in use.
    if need_server:
        if is_port_inuse(app.config.RPC_PORT) or \
           is_port_inuse(app.config.PUBSUB_PORT):
            err_msg = (
                'App fails to start services because '
                f'either port {app.config.RPC_PORT} or {app.config.PUBSUB_PORT} '
                'was already in use. '
                'Please check if there was another FeelUOwn instance.'
            )

    if err_msg:
        if app.mode & App.GuiMode:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            w = QMessageBox()
            w.setText(err_msg)
            w.finished.connect(lambda _: QApplication.quit())
            w.show()
        else:
            logger.error(err_msg)
            sys.exit(1)
        return

    if need_server:
        platform = sys.platform.lower()
        if platform == 'darwin':
            try:
                from .global_hotkey_mac import MacGlobalHotkeyManager
            except ImportError as e:
                logger.warning("Can't start mac hotkey listener: %s", str(e))
            else:
                mac_global_hotkey_mgr = MacGlobalHotkeyManager()
                mac_global_hotkey_mgr.start()
        elif platform == 'linux':
            from feeluown.linux import run_mpris2_server
            run_mpris2_server(app)

        asyncio.create_task(app.server.run(
            app.get_listen_addr(),
            app.config.RPC_PORT
        ))
        asyncio.create_task(asyncio.start_server(
            PubsubHandlerV1(app.pubsub_gateway).handle,
            host=app.get_listen_addr(),
            port=app.config.PUBSUB_PORT,
        ))

    if not need_window and not need_server:
        logger.warning('Fuo running with no daemon and no window')
