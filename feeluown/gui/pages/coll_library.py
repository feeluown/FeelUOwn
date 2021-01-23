from feeluown.models import ModelType
from feeluown.utils.reader import wrap
from feeluown.widgets.tabbar import Tab
from feeluown.containers.table import Renderer


async def render(req, **kwargs):
    app = req.ctx['app']
    tab_id = Tab(int(req.query.get('tab_id', Tab.songs.value)))

    ui = app.ui
    ui.right_panel.collection_container.hide()
    ui.right_panel.scrollarea.show()

    table_container = ui.right_panel.table_container
    renderer = LibraryRenderer(tab_id)
    await table_container.set_renderer(renderer)


class LibraryRenderer(Renderer):
    def __init__(self, tab_id):
        self.tab_id = tab_id

    async def render(self):
        mapping = {
            Tab.songs: (ModelType.song, self.show_songs,
                        self.tabbar.show_songs_needed),
            Tab.albums: (ModelType.album, self.show_albums,
                         self.tabbar.show_albums_needed),
            Tab.artists: (ModelType.artist, self.show_artists,
                          self.tabbar.show_artists_needed),
            Tab.playlists: (ModelType.playlist, self.show_playlists,
                            self.tabbar.show_playlists_needed),
            Tab.videos: (ModelType.video, self.show_videos,
                         self.tabbar.show_videos_needed),
        }

        for tab_id, (_, _, signal) in mapping.items():
            signal.connect(self.on_tab_id_activated(tab_id))

        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(self.tab_id)

        self.meta_widget.show()
        self.meta_widget.title = '音乐库'

        coll = self._app.coll_uimgr.get_coll_library()
        mtype, show_handle, _ = mapping.get(self.tab_id)
        models = []
        for model in coll.models:
            if model.meta.model_type == mtype:
                models.append(model)
        reader = wrap(models)
        show_handle(reader)

    def on_tab_id_activated(self, tab_id):
        def cb():
            if tab_id != self.tab_id:
                self.show_by_tab_id(tab_id)
        return cb

    def show_by_tab_id(self, tab_id):
        query = {'tab_id': tab_id.value}
        self._app.browser.goto(page='/colls/library', query=query)
