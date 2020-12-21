from feeluown.utils import aio
from feeluown.models.uri import resolve, ResolveFailed
from feeluown.containers.table import Renderer


async def render(req, provider, identifier, **kwargs):
    app = req.ctx['app']

    uri = f'fuo://{provider}/songs/{identifier}'
    try:
        song = resolve(uri)
    except ResolveFailed:
        return
    else:
        songs = await aio.run_in_executor(None, app.library.song_list_similar, song)
        renderer = SimilarSongsRenderer(songs)
        await app.ui.table_container.set_renderer(renderer)


class SimilarSongsRenderer(Renderer):

    def __init__(self, songs):
        self._songs = songs

    async def render(self):
        self.meta_widget.title = '相似歌曲'
        self.meta_widget.show()
        self.show_songs(songs=self._songs.copy())
