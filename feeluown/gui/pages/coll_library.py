from feeluown.models import ModelType
from feeluown.utils.reader import wrap
from feeluown.widgets.tabbar import Tab
from feeluown.gui.page_containers.table import Renderer

from feeluown.gui.base_renderer import LibraryTabRendererMixin


async def render(req, **kwargs):
    app = req.ctx['app']
    tab_id = Tab(int(req.query.get('tab_id', Tab.songs.value)))

    ui = app.ui
    ui.right_panel.set_body(ui.right_panel.scrollarea)

    table_container = ui.right_panel.table_container
    renderer = LibraryRenderer(tab_id)
    await table_container.set_renderer(renderer)


class LibraryRenderer(Renderer, LibraryTabRendererMixin):
    def __init__(self, tab_id):
        self.tab_id = tab_id

    async def render(self):
        self.init_tabbar_signal_binding()

        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(self.tab_id)

        self.meta_widget.show()
        self.meta_widget.title = '音乐库'

        coll = self._app.coll_uimgr.get_coll_library()
        mtype = self.get_tabid_mtype_mapping()[self.tab_id]
        models = [model for model in coll.models
                  if model.meta.model_type == mtype]
        reader = wrap(models)
        show_handler = self.get_tabid_handler_mapping()[self.tab_id]
        show_handler(reader)

    def show_by_tab_id(self, tab_id):
        query = {'tab_id': tab_id.value}
        self._app.browser.goto(page='/colls/library', query=query)

    def get_tabid_mtype_mapping(self):
        return {
            Tab.songs: ModelType.song,
            Tab.albums: ModelType.album,
            Tab.artists: ModelType.artist,
            Tab.playlists: ModelType.playlist,
            Tab.videos: ModelType.video,
        }
