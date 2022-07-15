import logging
import json
from contextlib import contextmanager
from typing import Optional, Type

from feeluown.consts import STATE_FILE
from feeluown.utils.request import Request
from feeluown.library import Library
from feeluown.utils.dispatch import Signal
from feeluown.models import (
    Resolver, reverse, resolve,
    ResolverNotFound,
)
from feeluown.player import (
    PlaybackMode, Playlist, LiveLyric,
    FM, Player, RecentlyPlayed
)
from feeluown.plugin import PluginsManager
from feeluown.version import VersionManager
from feeluown.task import TaskManager

from .mode import AppMode


logger = logging.getLogger(__name__)


class App:
    """App 基类"""
    _instance = None

    # .. deprecated:: 3.8
    #    Use :class:`AppMode` instead.
    DaemonMode = AppMode.server.value
    GuiMode = AppMode.gui.value
    CliMode = AppMode.cli.value

    def __init__(self, args, config):

        self.mode = config.MODE  # DEPRECATED: use app.config.MODE instead
        self.config = config
        self.args = args
        self.initialized = Signal()
        self.about_to_shutdown = Signal()

        self.plugin_mgr = PluginsManager(self)
        self.request = Request()  # TODO: rename request to http
        self.version_mgr = VersionManager(self)
        self.task_mgr = TaskManager(self)

        # Library.
        self.library = Library(config.PROVIDERS_STANDBY)
        # TODO: initialization should be moved into initialize
        Resolver.library = self.library

        # Player.
        self.player = Player(audio_device=bytes(config.MPV_AUDIO_DEVICE, 'utf-8'))
        self.playlist = Playlist(self, audio_select_policy=config.AUDIO_SELECT_POLICY)
        self.live_lyric = LiveLyric(self)
        self.fm = FM(self)
        self.recently_played = RecentlyPlayed(self.playlist)

        # TODO: initialization should be moved into initialize
        self.player.set_playlist(self.playlist)

        self.about_to_shutdown.connect(lambda _: self.dump_state(), weak=False)

    def initialize(self):
        self.player.position_changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed,
                                           aioqueue=True)
        self.plugin_mgr.scan()

    def run(self):
        pass

    @property
    def instance(self) -> Optional['App']:
        """App running instance.

        .. versionadded:: 3.8
        """
        return App._instance

    @property
    def has_server(self) -> bool:
        """
        .. versionadded:: 3.8
        """
        return AppMode.server in AppMode(self.config.MODE)

    @property
    def has_gui(self) -> bool:
        """
        .. versionadded:: 3.8
        """
        return AppMode.gui in AppMode(self.config.MODE)

    def show_msg(self, msg, *args, **kwargs):
        """在程序中显示消息，一般是用来显示程序当前状态"""
        # pylint: disable=no-self-use, unused-argument
        logger.info(msg)

    def get_listen_addr(self):
        return '0.0.0.0' if self.config.ALLOW_LAN_CONNECT else '127.0.0.1'

    def load_state(self):
        playlist = self.playlist
        player = self.player
        recently_played = self.recently_played

        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            logger.exception('invalid state file')
        else:
            player.volume = state['volume']

            # Restore recently_played states.
            recently_played_models = []
            for model in state.get('recently_played', []):
                try:
                    model = resolve(model)
                except ResolverNotFound:
                    pass
                else:
                    recently_played_models.append(model)
            recently_played.init_from_models(recently_played_models)

            # Restore playlist states.
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
        recently_played = self.recently_played

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
            'recently_played': [reverse(song, as_line=True)
                                for song in recently_played.list_songs()]
        }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
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
                show_msg(s + f'...{value}%', timeout=5000)

            def failed(self, msg=''):
                raise ActionError(msg)

        show_msg(s + '...', timeout=5000)  # doing
        try:
            yield Action()
        except ActionError as e:
            show_msg(s + f'...failed\t{str(e)}')
        except Exception as e:
            show_msg(s + f'...error\t{str(e)}')  # error
            raise
        else:
            show_msg(s + '...done')  # done

    def about_to_exit(self):
        logger.info('Do graceful shutdown')
        try:
            self.about_to_shutdown.emit(self)
            self.player.stop()
            self.exit_player()
        except:  # noqa, pylint: disable=bare-except
            logger.exception("about-to-exit failed")
        logger.info('Ready for shutdown')

    def exit_player(self):
        self.player.shutdown()  # this cause 'abort trap' on macOS

    def exit(self):
        self.about_to_exit()


def create_app(args, config) -> App:
    """App factory function.

    Do not add `create` function to :class:`App` because QWidget also has
    a `create` function.
    """
    need_server = AppMode.server in AppMode(config.MODE)
    need_window = AppMode.gui in AppMode(config.MODE)

    # pylint: disable=import-outside-toplevel,cyclic-import
    cls: Type[App]

    if args.cmd is not None:
        from feeluown.app.cli_app import CliApp
        cls = CliApp
    elif need_server and need_window:
        from feeluown.app.mixed_app import MixedApp
        cls = MixedApp
    elif need_window:
        from feeluown.app.gui_app import GuiApp
        cls = GuiApp
    elif need_server:
        from feeluown.app.server_app import ServerApp
        cls = ServerApp
    else:
        cls = App
    return cls(args, config)
