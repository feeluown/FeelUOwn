import logging
import json
from contextlib import contextmanager
from typing import Optional, Type

from feeluown.consts import STATE_FILE
from feeluown.utils.request import Request
from feeluown.library import Library
from feeluown.utils.dispatch import Signal
from feeluown.library import (
    Resolver, reverse, resolve,
    ResolverNotFound, ResolveFailed,
)
from feeluown.player import (
    PlaybackMode, Playlist, LiveLyric,
    FM, Player, RecentlyPlayed, PlayerPositionDelegate
)
from feeluown.collection import CollectionManager
from feeluown.plugin import plugins_mgr
from feeluown.version import VersionManager
from feeluown.task import TaskManager
from feeluown.alert import AlertManager

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

    def __init__(self, args, config, **kwargs):
        App._instance = self
        self.mode = config.MODE  # DEPRECATED: use app.config.MODE instead
        self.config = config
        self.args = args
        self.plugin_mgr = plugins_mgr

        self.initialized = Signal()
        # .. versionadded:: 3.8.11
        #    App started signal. Maybe the initialized signal can be removed?
        self.started = Signal()  # App is ready to use, for example, UI is available.
        self.about_to_shutdown = Signal()

        self.alert_mgr = AlertManager()
        self.request = Request()  # TODO: rename request to http
        self.version_mgr = VersionManager(self)
        self.task_mgr = TaskManager(self)
        # Library.
        self.library = Library(
            config.PROVIDERS_STANDBY,
            config.ENABLE_AI_STANDBY_MATCHER
        )
        self.coll_mgr = CollectionManager(self)
        self.ai = None
        try:
            from feeluown.ai import AI
        except ImportError as e:
            logger.warning(f"AI is not available, err: {e}")
        else:
            if (config.OPENAI_API_BASEURL and
                    config.OPENAI_API_KEY and
                    config.OPENAI_MODEL):
                self.ai = AI(
                    config.OPENAI_API_BASEURL,
                    config.OPENAI_API_KEY,
                    config.OPENAI_MODEL,
                )
                self.library.setup_ai(self.ai)
            else:
                logger.warning("AI is not available, no valid settings")

        if config.ENABLE_YTDL_AS_MEDIA_PROVIDER:
            try:
                self.library.setup_ytdl(rules=config.YTDL_RULES)
            except ImportError as e:
                logger.warning(f"can't enable ytdl as standby due to {e}")
            else:
                logger.warning('ytdl-as-standby is deprecated since v4.1.9')
                logger.info(f"enable ytdl as standby succeed"
                            f" with rules:{config.YTDL_RULES}")
        # TODO: initialization should be moved into initialize
        Resolver.library = self.library
        # Player.
        self.player = Player(
            audio_device=bytes(config.MPV_AUDIO_DEVICE, 'utf-8'),
            fade=config.PLAYBACK_CROSSFADE,
            fade_time_ms=config.PLAYBACK_CROSSFADE_DURATION,
        )
        # Theoretically, each caller maintain its own position delegate.
        # For simplicity, this delegate is created for common use cases and
        #
        # For progress slider and label in player bar, user may only see the difference
        # when it is greater than 1s. There are usually only one or two lines of lyrics
        # in one second. Considering the use cases and performance, I guess 300ms is
        # a reasonable interval.
        self.player_pos_per300ms = PlayerPositionDelegate(self.player, interval=300)
        self.playlist = Playlist(self, audio_select_policy=config.AUDIO_SELECT_POLICY)
        self.live_lyric = LiveLyric(self)
        self.fm = FM(self)
        self.recently_played = RecentlyPlayed(self.playlist)

        # TODO: initialization should be moved into initialize
        self.player.set_playlist(self.playlist)

        self.about_to_shutdown.connect(lambda _: self.dump_and_save_state(), weak=False)

    def initialize(self):
        self.coll_mgr.scan()
        self.alert_mgr.initialize(self)
        self.player_pos_per300ms.initialize()
        self.player_pos_per300ms.changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed,
                                           aioqueue=True)
        self.plugin_mgr.enable_plugins(self)

    def run(self):
        pass

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

    def apply_state(self, state):
        playlist = self.playlist
        player = self.player
        recently_played = self.recently_played

        if state:
            player.volume = state['volume']

            # Restore recently_played states.
            recently_played_models = []
            for model in state.get('recently_played', []):
                try:
                    model = resolve(model)
                except ResolverNotFound:
                    pass
                except ResolveFailed as e:
                    logger.warning(f'resolve failed, {e}')
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
                except ResolveFailed as e:
                    logger.warning(f'resolve failed, {e}')
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

    def load_state(self):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except FileNotFoundError:
            return {}
        except json.decoder.JSONDecodeError:
            logger.exception('invalid state file')
            return {}
        return state

    def load_and_apply_state(self):
        state = self.load_state()
        self.apply_state(state)

    def dump_state(self):
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
            # cast position to int to avoid such value 2.7755575615628914e-17
            'position': int(player.position or 0),
            'playlist': [reverse(song, as_line=True) for song in playlist.list()],
            'recently_played': [reverse(song, as_line=True)
                                for song in recently_played.list_songs()]
        }
        return state

    def dump_and_save_state(self):
        logger.info("Dump and save app state")
        state = self.dump_state()
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
            self.player_pos_per300ms.stop()
            self.player.stop()
            self.exit_player()
        except:  # noqa, pylint: disable=bare-except
            logger.exception("about-to-exit failed")
        logger.info('Ready for shutdown, or crash :)')

    def exit_player(self):
        self.player.shutdown()  # this cause 'abort trap' on macOS

    def exit(self):
        self.about_to_exit()


def get_app() -> Optional['App']:
    """
    .. versionadded:: 3.8.11
    """
    return App._instance


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
