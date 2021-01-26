from feeluown.utils import aio
from feeluown.gui.page_containers.table import Renderer


async def render(req, provider, identifier, **kwargs):
    app = req.ctx['app']
    song = req.ctx['model']
    songs = await aio.run_in_executor(None, app.library.song_list_similar, song)
    renderer = SimilarSongsRenderer(song, songs)
    await app.ui.table_container.set_renderer(renderer)


class SimilarSongsRenderer(Renderer):

    def __init__(self, song, songs):
        self._song = song
        self._songs = songs

    async def render(self):
        song = self._song
        song_str = f'{song.title_display} - {song.artists_name_display}'
        self.meta_widget.title = f'“{song_str}”的相似歌曲'
        self.meta_widget.show()
        self.show_songs(songs=self._songs.copy())
