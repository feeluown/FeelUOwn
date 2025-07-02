import logging
from typing import Optional, TYPE_CHECKING

from PyQt5.QtGui import QGuiApplication

from feeluown.excs import ProviderIOError
from feeluown.utils.aio import run_fn, run_afn
from feeluown.player import SongRadio
from feeluown.library import (
    SongModel, VideoModel, BriefSongModel,
    SupportsPlaylistAddSong, SupportsCurrentUserListPlaylists, SupportsCurrentUser,
)

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)


MV_BTN_TEXT = '播放 MV'


class SongMenuInitializer:

    def __init__(self, app: 'GuiApp', song):
        """
        :type app: feeluown.app.App
        """
        self._app = app
        self._song = song
        self._fetching_artists = False
        self._fetching_mv = False
        self._fetching_user_playlists = False

    def apply(self, menu):

        app = self._app
        song = self._song

        def enter_song_radio(song):
            radio = SongRadio.create(app, song)
            app.fm.activate(radio.fetch_songs_func, reset=False)
            if app.playlist.current_song != song:
                app.playlist.clear()
                self._app.playlist.next()
                self._app.player.resume()
            else:
                for song_ in app.playlist.list().copy():
                    if song_ is not app.playlist.current_song:
                        app.playlist.remove(song_)
                self._app.player.resume()

        def goto_song_explore(song):
            app.browser.goto(model=song, path='/explore')

        async def goto_song_album(song):
            usong: SongModel = await run_fn(self._app.library.song_upgrade, song)
            if usong.album is not None:
                self._app.browser.goto(model=usong.album)
            else:
                self._app.show_msg('该歌曲没有专辑信息')

        menu.hovered.connect(self.on_action_hovered)
        menu.addAction('搜索相似资源').triggered.connect(
            lambda: self.show_similar_resource(song))
        artist_menu = menu.addMenu('查看歌手')
        artist_menu.menuAction().setData({'artists': None, 'song': song})
        mv_menu = menu.addMenu(MV_BTN_TEXT)
        mv_menu.menuAction().setData({'mvs': None, 'song': song})

        menu.addAction('查看专辑').triggered.connect(
            lambda: run_afn(goto_song_album, song))
        menu.addAction('歌曲电台').triggered.connect(
            lambda: enter_song_radio(song))
        menu.addAction('歌曲详情').triggered.connect(
            lambda: goto_song_explore(song))

        menu.addSeparator()
        playlist_add_menu = menu.addMenu('加入到播放列表')
        playlist_add_menu.menuAction().setData(
            {'menu_id': 'playlist_add', 'playlists': None, 'song': song})

        ai_menu = menu.addMenu('AI')
        ai_menu.addAction('拷贝 AI Prompt').triggered.connect(
            lambda: self.copy_ai_prompt(song))

    def copy_ai_prompt(self, song):
        prompt = '你是一个音乐播放器助手。\n'
        prompt += '【填入你的需求】\n'
        prompt += f'歌曲信息如下 -> 歌曲名：{song.title}, 歌手名：{song.artists_name}'
        QGuiApplication.clipboard().setText(prompt)
        self._app.show_msg('已经复制到剪贴板')

    def show_similar_resource(self, song):
        from feeluown.gui.components.search import create_search_result_view

        view = create_search_result_view(self._app, song)
        view.show()

    def on_action_hovered(self, action):
        """
        Fetch song.artists when artists_action is hovered. If it is
        already fetched, ignore.
        """
        data = action.data()
        if data is None:  # submenu action
            return
        if 'artists' in data:
            self._hover_artists(action, data)
        elif 'mvs' in data:
            self._hover_mv(action, data)
        elif 'menu_id' in data and data['menu_id'] == 'playlist_add':
            if self._fetching_user_playlists is False:
                self._fetching_user_playlists = True
                self._app.task_mgr.run_afn_preemptive(
                    self._hover_playlist_add, action, data)

    async def _hover_playlist_add(self, action, data):
        # pylint: disable=unnecessary-direct-lambda-call
        logger.info('playlist-add action is hovered')
        if data['playlists'] is not None:
            return

        song: BriefSongModel = data['song']
        provider = self._app.library.get(song.source)

        async def add2p(provider: SupportsPlaylistAddSong, playlist, song):
            try:
                ok = await run_fn(provider.playlist_add_song, playlist, song)
            except ProviderIOError as e:
                logger.error(f"add song to playlist failed {e}")
                ok = False
            if ok:
                self._app.show_msg(f'已加入到 {playlist.name} ✅')
            else:
                self._app.show_msg(f'加入到 {playlist.name} 失败 ❌')

        if (
            isinstance(provider, SupportsPlaylistAddSong)
            and isinstance(provider, SupportsCurrentUser)
            and isinstance(provider, SupportsCurrentUserListPlaylists)
            and provider.has_current_user()
        ):
            try:
                playlists = await run_fn(provider.current_user_list_playlists)
            except ProviderIOError as e:
                logger.error(f"fetch user playlists failed {e}")
                playlists = []
            data['playlists'] = playlists
            action.setData(data)
            action.setEnabled(len(playlists) > 0)
            for playlist in playlists:
                try:
                    action_ = action.menu().addAction(playlist.name)
                    action_.triggered.connect(
                        (lambda p: lambda: run_afn(add2p, provider, p, song))(playlist))
                except RuntimeError:
                    # action may have been deleted.
                    return
        else:
            action.setEnabled(False)
        self._fetching_user_playlists = False

    def _hover_mv(self, action, data):

        def mv_fetched_cb(future):
            self._fetching_mv = False
            try:
                mv: Optional[VideoModel] = future.result()
            except ProviderIOError as e:
                logger.error(f"fetch song mv failed {e}")
                mv = None
            if mv is not None:
                try:
                    mv_action = action.menu().addAction(mv.title)
                    mv_action.triggered.connect(
                        lambda: self._app.playlist.play_model(mv))
                except RuntimeError:
                    # action may have been deleted.
                    return
            if mv is not None:
                data['mvs'] = [mv]
                action.setText(MV_BTN_TEXT)
            else:
                data['mvs'] = []
                action.setText('该歌曲无 MV')
                action.setDisabled(True)
            action.setData(data)

        # artists value has not been fetched
        if data['mvs'] is None and self._fetching_mv is False:
            logger.debug('fetch song.mv for actions')
            song = data['song']
            self._fetching_mv = True
            task = run_fn(self._app.library.song_get_mv, song)
            task.add_done_callback(mv_fetched_cb)

    def _hover_artists(self, action, data):
        # pylint: disable=unnecessary-direct-lambda-call

        def artists_fetched_cb(future):
            self._fetching_artists = False
            artists = future.result()  # ignore the potential exception
            if artists:
                for artist in artists:
                    try:
                        artist_action = action.menu().addAction(artist.name)
                        # create a closure to bind variable artist
                        artist_action.triggered.connect(
                            (lambda x: lambda: self._app.browser.goto(model=x))(artist))
                    except RuntimeError:
                        # action may have been deleted.
                        return
            data['artists'] = artists or []
            action.setData(data)

        # artists value has not been fetched
        if data['artists'] is None and self._fetching_artists is False:
            logger.debug('fetch song.artists for actions')
            song = data['song']
            self._fetching_artists = True
            task = run_fn(lambda: self._app.library.song_upgrade(song).artists)
            task.add_done_callback(artists_fetched_cb)
