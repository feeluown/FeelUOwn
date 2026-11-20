from feeluown.utils.aio import run_afn
from feeluown.utils.reader import create_reader
from feeluown.gui.page_containers.table import Renderer
from .template import render_error_message


async def render(req, identifier, **kwargs):
    app = req.ctx["app"]
    playlist = app.smart_mgr.get(identifier)
    if playlist is None:
        await render_error_message(app, f'Smart playlist not found: {identifier}')
        return
    app.smart_mgr.set_active(identifier)
    right_panel = app.ui.right_panel
    right_panel.set_body(right_panel.table_container)
    await run_afn(
        app.ui.table_container.set_renderer,
        SmartPlaylistRenderer(app, playlist),
    )


class SmartPlaylistRenderer(Renderer):
    def __init__(self, app, smart_playlist):
        self._app = app
        self._smart = smart_playlist

    async def render(self):
        self.meta_widget.title = self._smart.name
        self.meta_widget.source = self._smart.description
        self.meta_widget.show()
        songs = self._app.smart_mgr.evaluate(self._smart.rule)
        self.meta_widget.songs_count = len(songs)
        reader = create_reader(songs)
        self.show_songs(reader)
        self.toolbar.show()
