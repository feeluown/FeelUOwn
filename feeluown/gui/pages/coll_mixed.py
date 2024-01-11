from feeluown.app.gui_app import GuiApp
from feeluown.collection import CollectionType, Collection
from feeluown.library import ModelType
from feeluown.utils.reader import wrap
from feeluown.gui.page_containers.table import Renderer

from feeluown.gui.base_renderer import TabBarRendererMixin


async def render(req, identifier, **kwargs):
    app: GuiApp = req.ctx['app']
    ui = app.ui
    tab_index = int(req.query.get('tab_index', 0))

    coll = app.coll_mgr.get(identifier)

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
    def __init__(self, app, tab_index, coll: Collection):
        self._app = app
        self._coll = coll
        self.tab_index = tab_index
        self.tabs = self.default_tabs()

    async def render(self):
        coll = self._coll
        self.meta_widget.show()
        if coll.type is CollectionType.sys_library:
            self.meta_widget.title = '音乐库'
        else:
            self.meta_widget.title = coll.name
        self.render_tab_bar()
        self.render_models()

        def remove_song(model):
            # TODO(cosven): the whole UI is refreshed after a model is removed,
            # ideally, only part of the UI is refreshed. For example, a user scroll
            # to the bottom of the list view, when the last model is removed,
            # the UI is refreshed and the the user needs to scroll to the bottom again.
            self._coll.remove(model)
            self.render_models()
            self._app.show_msg('移除歌曲成功')

        if self.tabs[self.tab_index][1] is ModelType.song:
            self.songs_table.remove_song_func = remove_song

    def render_by_tab_index(self, tab_index):
        self._app.browser.goto(page=f'/colls/{self._coll.identifier}',
                               query={'tab_index': tab_index})

    def render_models(self):
        _, mtype, show_handler = self.tabs[self.tab_index]
        models = [model for model in self._coll.models
                  if model.meta.model_type == mtype]
        reader = wrap(models)
        show_handler(reader)
