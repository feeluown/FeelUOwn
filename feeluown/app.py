import asyncio
import logging
from functools import partial
from contextlib import contextmanager

from fuocore import LiveLyric, Library
from fuocore.pubsub import run as run_pubsub

from .config import config
from .consts import APP_ICON
from .protocol import FuoProcotol
from .player import Player
from .plugin import PluginsManager
from .publishers import LiveLyricPublisher
from .request import Request
from .version import VersionManager


logger = logging.getLogger(__name__)


class App:
    """App 基类"""

    CliMode = 0x0001
    GuiMode = 0x0010

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

        class Action:
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

    def shutdown(self):
        self.pubsub_server.close()
        self.player.stop()
        self.player.shutdown()


def attach_attrs(app, **player_kwargs):
    """初始化 app 属性"""
    app.library = Library()
    app.live_lyric = LiveLyric()
    app.protocol = FuoProcotol(app)
    app.plugin_mgr = PluginsManager(app)
    app.version_mgr = VersionManager(app)
    app.request = Request()
    app._g = {}

    app.player = Player(app=app, **(player_kwargs or {}))
    app.playlist = app.player.playlist

    if app.mode & app.GuiMode:
        from feeluown.components.history import HistoriesModel
        from feeluown.components.provider import ProvidersModel
        from feeluown.components.playlists import PlaylistsModel
        from feeluown.components.my_music import MyMusicModel
        from feeluown.components.collections import CollectionsModel
        from feeluown.protocol import CollectionManager

        from .browser import Browser
        from .hotkey import HotkeyManager
        from .image import ImgManager
        from .theme import ThemeManager
        from .tips import TipsManager
        from .ui import Ui

        app.coll_mgr = CollectionManager(app)
        app.theme_mgr = ThemeManager(app)
        app.tips_mgr = TipsManager(app)
        app.hotkey_mgr = HotkeyManager(app)
        app.img_mgr = ImgManager(app)
        app.playlists = PlaylistsModel(parent=app)
        app.histories = HistoriesModel(parent=app)
        app.providers = ProvidersModel(parent=app)
        app.my_music = MyMusicModel(parent=app)
        app.collections = CollectionsModel(parent=app)
        app.browser = Browser(app)
        app.ui = Ui(app)
        app.show_msg = app.ui.magicbox.show_msg


def initialize(app):
    app.player.position_changed.connect(app.live_lyric.on_position_changed)
    app.playlist.song_changed.connect(app.live_lyric.on_song_changed)
    app.pubsub_gateway, app.pubsub_server = run_pubsub()
    app.plugin_mgr.scan()
    app.protocol.run_server()
    if app.mode & App.GuiMode:
        app.theme_mgr.load_light()
        app.tips_mgr.show_random_tip()
        app.coll_mgr.scan()

    app._ll_publisher = LiveLyricPublisher(app.pubsub_gateway)
    app.live_lyric.sentence_changed.connect(app._ll_publisher.publish)
    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(loop.create_task, app.version_mgr.check_release()))


def create_app(mode, **player_kwargs):
    bases = [App]

    if mode & App.GuiMode:
        from PyQt5.QtGui import QIcon
        from PyQt5.QtWidgets import QApplication, QWidget

        class GuiApp(QWidget):
            mode = App.GuiMode

            def __init__(self):
                super().__init__()
                self.resize(1000, 618)
                self.setObjectName('app')
                QApplication.setWindowIcon(QIcon(APP_ICON))

            def closeEvent(self, e):
                try:
                    app.ui.mpv_widget.close()
                    self.shutdown()
                finally:
                    QApplication.quit()

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
    attach_attrs(app, **player_kwargs)
    initialize(app)
    if app.mode & App.GuiMode:
        app.show()
    return app
