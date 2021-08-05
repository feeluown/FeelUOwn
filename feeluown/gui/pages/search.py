from feeluown.utils.reader import wrap
from feeluown.models import SearchType
from feeluown.gui.widgets.magicbox import KeySourceIn, KeyType
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.base_renderer import TabBarRendererMixin


async def render(req, **kwargs):
    """/search handler

    :type app: feeluown.app.App
    """
    q = req.query.get('q', '')
    if not q:
        return

    app = req.ctx['app']
    ui = app.ui

    tab_index = int(req.query.get('tab_index', 0))
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None

    right_panel = ui.right_panel
    table_container = right_panel.table_container
    right_panel.set_body(right_panel.scrollarea)

    renderer = SearchResultRenderer(q, tab_index, source_in=source_in)
    await table_container.set_renderer(renderer)


class SearchResultRenderer(Renderer, TabBarRendererMixin):
    def __init__(self, q, tab_index, source_in=None):
        self.q = q
        self.tab_index = tab_index
        self.source_in = source_in

        self.tabs = [
            ('歌曲', SearchType.so, 'songs', self.show_songs),
            ('专辑', SearchType.al, 'albums', self.show_albums),
            ('歌手', SearchType.ar, 'artists', self.show_artists),
            ('歌单', SearchType.pl, 'playlists', self.show_playlists),
            ('视频', SearchType.vi, 'videos', self.show_videos),
        ]

    async def render(self):
        self.meta_widget.show()
        self.meta_widget.title = '搜索 “{}”'.format(self.q)
        self.render_tab_bar()

        _, search_type, attrname, show_handler = self.tabs[self.tab_index]

        async def models_g():
            async for result in self._app.library.a_search(
                    self.q, source_in=self.source_in, type_in=search_type):
                if result is not None:
                    for obj in (getattr(result, attrname) or []):
                        yield obj

        show_handler(reader=wrap(models_g()))
        self.toolbar.hide()

    def render_by_tab_index(self, tab_index):
        search_type = self.tabs[tab_index][1]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {'q': self.q, 'tab_index': tab_index}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query['source_in'] = source_in
        self._app.browser.goto(page='/search', query=query)
