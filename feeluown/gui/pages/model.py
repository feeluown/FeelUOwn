from feeluown.gui.page_containers.table import Renderer
from feeluown.utils import aio
from feeluown.models import ModelType
from feeluown.models.uri import reverse


async def render(req, **kwargs):
    app = req.ctx['app']
    model = req.ctx['model']

    if model.meta.model_type == ModelType.song:
        model = await aio.run_in_executor(None, app.library.song_upgrade, model)
        renderer = SongRenderer(model)
        await app.ui.table_container.set_renderer(renderer)
    else:
        app.ui.right_panel.show_model(model)


class SongRenderer(Renderer):
    def __init__(self, song):
        self._song = song

    async def render(self):
        song = self._song
        self.meta_widget.title = f'{song.title}'
        self.meta_widget.subtitle = f'{song.artists_name} - {song.album_name}'
        self.meta_widget.show()

        brief_album = song.album
        album = self._app.library.cast_model_to_v1(brief_album)
        cover = await aio.run_in_executor(None, lambda: album.cover)
        if cover:
            await self.show_cover(cover, f'{reverse(album)}/cover')
