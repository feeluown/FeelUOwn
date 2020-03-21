from fuocore.reader import wrap
from fuocore.models import SearchType
from feeluown.widgets.tabbar import Tab
from feeluown.containers.table import Renderer


TypeTabMapping = {
    SearchType.so: Tab.songs,
    SearchType.al: Tab.albums,
    SearchType.ar: Tab.artists,
    SearchType.pl: Tab.playlists,
}


async def render(req, **kwargs):
    """

    :type app: feeluown.app.App
    """
    q = req.query.get('q', '')
    if not q:
        return
    type_ = req.query.get('type', None)
    type_ = SearchType.parse(type_) if type_ else SearchType.so

    app = req.ctx['app']
    ui = app.ui
    right_panel = ui.right_panel
    table_container = right_panel.table_container

    right_panel.collection_container.hide()
    right_panel.scrollarea.show()

    reader = wrap(await app.library.a_search(q, type_in=type_))
    renderer = SearchResultRenderer(q, type_, reader)
    await table_container.set_renderer(renderer)


class SearchResultRenderer(Renderer):
    def __init__(self, q, type_, reader):
        self.q = q
        self.type_ = type_
        self.reader = reader

    async def render(self):
        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(TypeTabMapping[self.type_])

        self.meta_widget.show()
        self.meta_widget.title = '搜索 “{}”'.format(self.q)

        self._bind_signals()

        mapping = {
            SearchType.so: ('songs', self.show_songs),
            SearchType.al: ('albums', self.show_albums),
            # SearchType.ar: ('artists', self.show_artists),
            # SearchType.pl: ('playlists', self.show_playlists),
        }

        attr, show_handler = mapping[self.type_]

        objects = []
        for result in self.reader:
            objects.extend(getattr(result, attr) or [])
        show_handler(objects)

    def _bind_signals(self):
        self.tabbar.show_songs_needed.connect(self._show(SearchType.so))
        self.tabbar.show_albums_needed.connect(self._show(SearchType.al))

    def _show(self, type_):
        def cb():
            self._app.browser.goto(
                uri='/search',
                query={'q': self.q, 'type': type_.value}
            )
        return cb