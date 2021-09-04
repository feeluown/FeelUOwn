import logging

from feeluown.utils import aio
from feeluown.player import SongRadio

logger = logging.getLogger(__name__)


class SongMenuInitializer:

    def __init__(self, app, song):
        """
        :type app: feeluown.app.App
        """
        self._app = app
        self._song = song
        self._fetching_artists = False

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
                for song in app.playlist.list().copy():
                    if song is not app.playlist.current_song:
                        app.playlist.remove(song)
                self._app.player.resume()

        def goto_song_explore(song):
            app.browser.goto(model=song, path='/explore')

        async def goto_song_album(song):
            song = await aio.run_fn(self._app.library.song_upgrade, song)
            album = await aio.run_fn(lambda: song.album)
            self._app.browser.goto(model=album)

        menu.hovered.connect(self.on_action_hovered)
        artist_menu = menu.addMenu('查看歌手')
        artist_menu.menuAction().setData({'artists': None, 'song': song})

        menu.addAction('查看专辑').triggered.connect(
            lambda: aio.run_afn(goto_song_album, song))
        menu.addAction('歌曲电台').triggered.connect(
            lambda: enter_song_radio(song))
        menu.addAction('歌曲详情').triggered.connect(
            lambda: goto_song_explore(song))

    def on_action_hovered(self, action):
        """
        Fetch song.artists when artists_action is hovered. If it is
        already fetched, ignore.
        """
        data = action.data()
        if data is None:  # submenu action
            return

        def artists_fetched_cb(future):
            self._fetching_artists = False
            artists = future.result()  # ignore the potential exception
            if artists:
                for artist in artists:
                    artist_action = action.menu().addAction(artist.name)
                    # create a closure to bind variable artist
                    artist_action.triggered.connect(
                        (lambda x: lambda: self._app.browser.goto(model=x))(artist))
            data['artists'] = artists or []
            action.setData(data)

        # the action is artists_action
        if 'artists' in data:
            # artists value has not been fetched
            if data['artists'] is None and self._fetching_artists is False:
                logger.debug('fetch song.artists for actions')
                song = data['song']
                self._fetching_artists = True
                task = aio.run_in_executor(
                    None, lambda: self._app.library.song_upgrade(song).artists)
                task.add_done_callback(artists_fetched_cb)
