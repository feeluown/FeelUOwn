from feeluown.collection import CollectionType
from feeluown.models import ModelType
from feeluown.utils.reader import wrap
from feeluown.gui.page_containers.table import Renderer

from feeluown.gui.base_renderer import TabBarRendererMixin


async def render(req, identifier, **kwargs):
    app = req.ctx['app']
    ui = app.ui
    tab_index = int(req.query.get('tab_index', 0))

    coll = app.coll_uimgr.get(int(identifier))

    mixed = False
    model_type = None
    if coll.type is CollectionType.sys_library:
        mixed = True
    else:
        types = set()
        for model in coll.models:
            types.add(model.meta.model_type)
            if len(types) >= 2:
                mixed = True
                break
        if types:
            model_type = types.pop()
        else:
            model_type = ModelType.song

    if mixed is True:
        ui.right_panel.set_body(ui.right_panel.scrollarea)
        table_container = ui.right_panel.table_container
        renderer = LibraryRenderer(app, tab_index, coll)
        await table_container.set_renderer(renderer)
    else:
        ui.right_panel.show_collection(coll, model_type)


class LibraryRenderer(Renderer, TabBarRendererMixin):
    """
    This Renderer was used to render library collection particularlly.

    TODO: create a more elegant renderer for mixed collection.
    NOTE(cosven): I think mixed collection should be rendered in single page
    without tab.
    """
    def __init__(self, app, tab_index, coll):
        self._app = app
        self._coll = coll
        self.tab_index = tab_index
        self.tabs = [
            ('歌曲', ModelType.song, self.show_songs),
            ('专辑', ModelType.album, self.show_albums),
            ('歌手', ModelType.artist, self.show_artists),
            ('歌单', ModelType.playlist, self.show_playlists),
            ('视频', ModelType.video, self.show_videos)
        ]

    async def render(self):
        coll = self._coll
        self.meta_widget.show()
        if coll.type is CollectionType.sys_library:
            self.meta_widget.title = '音乐库'
        else:
            self.meta_widget.title = coll.name
        self.render_tab_bar()

        _, mtype, show_handler = self.tabs[self.tab_index]
        models = [model for model in coll.models
                  if model.meta.model_type == mtype]
        reader = wrap(models)
        show_handler(reader)

    def render_by_tab_index(self, tab_index):
        coll_id = self._app.coll_uimgr.get_coll_id(self._coll)
        self._app.browser.goto(page=f'/colls/{coll_id}',
                               query={'tab_index': tab_index})
