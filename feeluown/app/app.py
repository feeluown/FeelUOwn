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

from feeluown.utils.request import Request
from feeluown.utils.utils import is_port_inuse
from .consts import STATE_FILE
from .player import FM, Player
from .plugin import PluginsManager
from .version import VersionManager
from .task import TaskManager


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

        self.plugin_mgr = PluginsManager(self)
        self.request = Request()  # TODO: rename request to http
        self.version_mgr = VersionManager(self)

        # Library.
        self.library = Library(config.PROVIDERS_STANDBY)
        # TODO: initialization should be moved into initialize
        Resolver.library = self.library

        # Player.
        self.playlist = Playlist(self, audio_select_policy=config.AUDIO_SELECT_POLICY)
        self.player = Player(audio_device=bytes(config.MPV_AUDIO_DEVICE, 'utf-8'))
        self.live_lyric = LiveLyric(self)
        self.fm = FM(self)

        self.task_mgr = TaskManager(self)

        # TODO: initialization should be moved into initialize
        self.player.set_playlist(self.playlist)

        self.about_to_shutdown.connect(lambda _: self.dump_state(), weak=False)

    @classmethod
    def create(cls, config) -> 'App':
        need_server = config.mode & cls.DaemonMode
        need_window = config.mode & cls.GuiMode
        if need_server and need_window:
            from feeluown.app.mixed_app import MixedApp
            app = MixedApp(config)
        elif need_window:
            from feeluown.app.gui_app import GuiApp
            app = GuiApp(config)
        elif need_server:
            from feeluown.app.server_app import ServerApp
            app = ServerApp(config)
        else:
            app = App(config)
        return app

    def initialize(self):
        self.player.position_changed.connect(self.live_lyric.on_position_changed)
        self.playlist.song_changed.connect(self.live_lyric.on_song_changed, aioqueue=True)

        self.task_mgr.initialize()
        self.plugin_mgr.scan()
        self.version_mgr.initialize()

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
