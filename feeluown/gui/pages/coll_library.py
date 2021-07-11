from feeluown.models import ModelType
from feeluown.utils.reader import wrap
from feeluown.gui.page_containers.table import Renderer

from feeluown.gui.base_renderer import TabBarRendererMixin


async def render(req, **kwargs):
    app = req.ctx['app']
    ui = app.ui
    tab_index = int(req.query.get('tab_index', 0))
    ui.right_panel.set_body(ui.right_panel.scrollarea)
    table_container = ui.right_panel.table_container
    renderer = LibraryRenderer(tab_index)
    await table_container.set_renderer(renderer)


class LibraryRenderer(Renderer, TabBarRendererMixin):

    def __init__(self, tab_index):
        self.tab_index = tab_index
        self.tabs = [
            ('歌曲', ModelType.song, self.show_songs),
            ('专辑', ModelType.album, self.show_albums),
            ('歌手', ModelType.artist, self.show_artists),
            ('歌单', ModelType.playlist, self.show_playlists),
            ('视频', ModelType.video, self.show_videos)
        ]

    async def render(self):
        self.meta_widget.show()
        self.meta_widget.title = '音乐库'
        self.render_tab_bar()

        coll = self._app.coll_uimgr.get_coll_library()
        _, mtype, show_handler = self.tabs[self.tab_index]
        models = [model for model in coll.models
                  if model.meta.model_type == mtype]
        reader = wrap(models)
        show_handler(reader)

    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(page='/colls/library',
                               query={'tab_index': tab_index})
