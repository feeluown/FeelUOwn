import asyncio
import logging
from functools import partial
from contextlib import contextmanager

from fuocore import LiveLyric, Library
from fuocore.pubsub import run as run_pubsub

from .consts import APP_ICON
from .player import Player
from .plugin import PluginsManager
from .server import FuoServer
from .publishers import LiveLyricPublisher
from .request import Request
from .version import VersionManager


logger = logging.getLogger(__name__)


class App:
    """App 基类"""

    DaemonMode = 0x0001  # 开启 daemon
    GuiMode = 0x0010     # 显示 GUI
    CliMode = 0x0100     # 命令行模式

    def exec_(self, code):
        """执行 Python 代码"""
        obj = compile(code, '<string>', 'single')
        self._g.update({
            'app': self,
            'player': self.player
        })
        exec(obj, self._g, self._g)

    def show_msg(self, msg, *args, **kwargs):
        """在程序中显示消息，一般是用来显示程序当前状态"""
        logger.info(msg)

    @contextmanager
    def create_action(self, s):
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

    def shutdown(self):
        if self.mode & App.DaemonMode:
            self.pubsub_server.close()
        self.player.stop()
        self.player.shutdown()


def attach_attrs(app):
    """初始化 app 属性"""
    app.library = Library()
    app.live_lyric = LiveLyric()
    player_kwargs = dict(
        audio_device=bytes(app.config.MPV_AUDIO_DEVICE, 'utf-8')
    )
    app.player = Player(app=app, **(player_kwargs or {}))
    app.playlist = app.player.playlist
    app.plugin_mgr = PluginsManager(app)
    app.request = Request()
    app._g = {}

    if app.mode & (app.DaemonMode | app.GuiMode):
        app.version_mgr = VersionManager(app)

    if app.mode & app.GuiMode:
        from feeluown.widgets.collections import CollectionsModel
        from feeluown.uimodels.provider import ProviderUiManager
        from feeluown.uimodels.playlist import PlaylistUiManager
        from feeluown.uimodels.my_music import MyMusicUiManager
        from feeluown.uimodels.collection import CollectionUiManager
        from feeluown.collection import CollectionManager

        from .browser import Browser
        from .hotkey import HotkeyManager
        from .image import ImgManager
        from .theme import ThemeManager
        from .tips import TipsManager
        from .ui import Ui

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
        app.show_msg = app.ui.magicbox.show_msg


def initialize(app):
    app.player.position_changed.connect(app.live_lyric.on_position_changed)
    app.playlist.song_changed.connect(app.live_lyric.on_song_changed)
    app.plugin_mgr.scan()
    if app.mode & app.DaemonMode:
        app.server = FuoServer(library=app.library,
                               player=app.player,
                               playlist=app.playlist,
                               live_lyric=app.live_lyric)
        app.pubsub_gateway, app.pubsub_server = run_pubsub()
        app.server.run()
        app._ll_publisher = LiveLyricPublisher(app.pubsub_gateway)
        app.live_lyric.sentence_changed.connect(app._ll_publisher.publish)

    if app.mode & App.GuiMode:
        app.theme_mgr.autoload()
        app.tips_mgr.show_random_tip()
        app.coll_uimgr.initialize()

    if app.mode & (App.DaemonMode | App.GuiMode):
        loop = asyncio.get_event_loop()
        loop.call_later(10, partial(loop.create_task, app.version_mgr.check_release()))


def create_app(config):
    bases = [App]

    mode = config.MODE
    if mode & App.GuiMode:
        from PyQt5.QtGui import QIcon, QPixmap
        from PyQt5.QtWidgets import QApplication, QWidget

        class GuiApp(QWidget):
            mode = App.GuiMode

            def __init__(self):
                super().__init__()
                self.resize(1000, 618)
                self.setObjectName('app')
                QApplication.setWindowIcon(QIcon(QPixmap(APP_ICON)))

            def closeEvent(self, e):
                app.ui.mpv_widget.close()
                event_loop = asyncio.get_event_loop()
                event_loop.stop()
                # try:
                #     self.shutdown()
                # finally:
                #     QApplication.quit()

        bases.append(GuiApp)

    if mode & App.CliMode:

        class CliApp:
            pass

        bases.append(CliApp)

    class FApp(*bases):
        def __init__(self, mode):
            for base in bases:
                base.__init__(self)
            self.mode = mode

    app = FApp(mode)
    app.config = config
    attach_attrs(app)
    if app.mode & App.GuiMode:
        app.show()
    initialize(app)
    return app
