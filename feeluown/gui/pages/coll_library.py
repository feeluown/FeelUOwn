from feeluown.models import ModelType
from feeluown.utils.reader import wrap
from feeluown.gui.widgets.tabbar import Tab, TabBar
from feeluown.gui.page_containers.table import Renderer

from feeluown.gui.base_renderer import LibraryTabRendererMixin


async def render(req, **kwargs):
    app = req.ctx['app']
    tab_index = int(req.query.get('tab_index', 0))

    ui = app.ui
    ui.right_panel.set_body(ui.right_panel.scrollarea)

    tabbar = TabBar()
    ui.toolbar.add_stacked_widget(tabbar)
    ui.toolbar.set_top_stacked_widget(tabbar)
    mapping = [('歌曲', Tab.songs),
                ('专辑', Tab.albums),
                ('歌手', Tab.artists),
                ('歌单', Tab.playlists),
                ('视频', Tab.videos)]

    target_tab_id = None
    for i, (tab_name, tab_id) in enumerate(mapping):
        tabbar.addTab(tab_name)
        if i == tab_index:
            target_tab_id = tab_id

    tabbar.setCurrentIndex(tab_index)
    tabbar.tabBarClicked.connect(
        lambda tab_index: app.browser.goto(page='/colls/library',
                                           query={'tab_index': tab_index}))

    table_container = ui.right_panel.table_container
    renderer = LibraryRenderer(target_tab_id)
    await table_container.set_renderer(renderer)


class LibraryRenderer(Renderer, LibraryTabRendererMixin):
    def __init__(self, tab_id):
        self.tab_id = tab_id

    async def render(self):
        self.render_tabbar()

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
