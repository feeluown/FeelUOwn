from PyQt5.QtWidgets import QWidget, QVBoxLayout

from feeluown.models import SearchType
from feeluown.gui.page_containers.table import TableContainer, Renderer
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.widgets.imglist import ImgListView
from feeluown.gui.widgets.songs import SongsTableView
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.widgets.magicbox import KeySourceIn, KeyType
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.accordion import Accordion
from feeluown.utils.reader import create_reader


async def render(req, **kwargs):  # pylint: disable=too-many-locals
    """/search handler

    :type app: feeluown.app.App
    """
    q = req.query.get('q', '')
    if not q:
        return

    tab_index = int(req.query.get('tab_index', 0))
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None

    app = req.ctx['app']

    body = Body()
    view = View(app, q)
    body.setWidget(view)
    app.ui.right_panel.set_body(body)

    search_type = [SearchType.so,
                   SearchType.al,
                   SearchType.ar,
                   SearchType.pl,
                   SearchType.vi][tab_index]

    is_first = True
    async for result in app.library.a_search(q, type_in=search_type):
        if result is not None:
            table_container = TableContainer(app, view.accordion)

            # HACK: set fixed row for tables.
            # pylint: disable=protected-access
            for table in table_container._tables:
                if isinstance(table, ImgListView):
                    table._fixed_row_count = 2
                    table.img_min_width = 100
                elif isinstance(table, SongsTableView):
                    table._fixed_row_count = 8
                    table._row_height = table.verticalHeader().defaultSectionSize()

            table_container.layout().setContentsMargins(0, 0, 0, 0)

            renderer = SearchResultRenderer(q, tab_index, source_in=source_in)
            await table_container.set_renderer(renderer)

            _, search_type, attrname, show_handler = renderer.tabs[tab_index]
            objects = getattr(result, attrname) or []
            show_handler(create_reader(objects))

            if is_first is False:
                table_container.hide()

            renderer.meta_widget.hide()
            renderer.toolbar.hide()

            provider = app.library.get(result.source)
            provider_name = result.source if provider is None else provider.name
            view.accordion.add_section(MidHeader(provider_name), table_container, 6, 12)
            is_first = False


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
        self.render_tab_bar()

    def render_by_tab_index(self, tab_index):
        search_type = self.tabs[tab_index][1]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {'q': self.q, 'tab_index': tab_index}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query['source_in'] = source_in
        self._app.browser.goto(page='/search', query=query)


class Body(ScrollArea):
    def page_overlay_height(self):
        return 30 + self.widget().title.height() + 10


class View(QWidget):
    def __init__(self, app, q):
        super().__init__()

        self._app = app

        self.title = LargeHeader(f'搜索“{q}”')
        self.accordion = Accordion()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 0, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(30)
        self._layout.addWidget(self.title)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.accordion)
        self._layout.addStretch(0)
