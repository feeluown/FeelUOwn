from datetime import datetime
from PyQt5.QtWidgets import QAbstractItemView, QFrame, QVBoxLayout

from feeluown.library import SearchType
from feeluown.gui.page_containers.table import TableContainer, Renderer
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.widgets.img_card_list import ImgCardListDelegate
from feeluown.gui.widgets.songs import SongsTableView, ColumnsMode
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.helpers import BgTransparentMixin
from feeluown.gui.widgets.magicbox import KeySourceIn, KeyType
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.accordion import Accordion
from feeluown.gui.widgets.labels import MessageLabel
from feeluown.utils.reader import create_reader
from feeluown.utils.router import Request
from feeluown.app.gui_app import GuiApp

Tabs = [('歌曲', SearchType.so),
        ('专辑', SearchType.al),
        ('歌手', SearchType.ar),
        ('歌单', SearchType.pl),
        ('视频', SearchType.vi)]


def get_tab_idx(search_type):
    for i, tab in enumerate(Tabs):
        if tab[1] == search_type:
            return i
    raise ValueError("unknown search type")


def get_source_in(req: Request):
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None
    return source_in


async def render(req: Request, **kwargs):
    """/search handler

    :type app: feeluown.app.App
    """
    # pylint: disable=too-many-locals,too-many-branches
    q = req.query.get('q', '')
    if not q:
        return

    app: 'GuiApp' = req.ctx['app']
    source_in = get_source_in(req)
    search_type = SearchType(req.query.get('type', SearchType.so.value))

    body = Body()
    view = View(app, q)
    body.setWidget(view)
    app.ui.right_panel.set_body(body)

    tab_index = get_tab_idx(search_type)
    succeed = 0
    start = datetime.now()
    is_first = True  # Is first search result.
    view.hint.show_msg('正在搜索...')
    async for result in app.library.a_search(
            q, type_in=search_type, source_in=source_in):
        table_container = TableContainer(app, view.accordion)
        table_container.layout().setContentsMargins(0, 0, 0, 0)

        # HACK: set fixed row for tables.
        # pylint: disable=protected-access
        for table in table_container._tables:
            assert isinstance(table, QAbstractItemView)
            delegate = table.itemDelegate()
            if isinstance(delegate, ImgCardListDelegate):
                # FIXME: set fixed_row_count in better way.
                table._fixed_row_count = 2  # type: ignore[attr-defined]
                delegate.update_settings("card_min_width", 140)
            elif isinstance(table, SongsTableView):
                table._fixed_row_count = 8
                table._row_height = table.verticalHeader().defaultSectionSize()

        renderer = SearchResultRenderer(q, tab_index, source_in=source_in)
        await table_container.set_renderer(renderer)
        _, search_type, attrname, show_handler = renderer.tabs[tab_index]
        objects = getattr(result, attrname) or []
        if not objects:  # Result is empty.
            continue

        succeed += 1
        if search_type is SearchType.so:
            show_handler(  # type: ignore[operator]
                create_reader(objects), columns_mode=ColumnsMode.playlist)
        else:
            show_handler(create_reader(objects))  # type: ignore[operator]
        source = objects[0].source
        provider = app.library.get(source)
        provider_name = provider.name
        if is_first is False:
            table_container.hide()
        view.accordion.add_section(MidHeader(provider_name), table_container, 6, 12)
        renderer.meta_widget.hide()
        renderer.toolbar.hide()
        is_first = False
    time_cost = (datetime.now() - start).total_seconds()
    view.hint.show_msg(f'搜索完成，共有 {succeed} 个有效的结果，花费 {time_cost:.2f}s')


class SearchResultRenderer(Renderer, TabBarRendererMixin):
    def __init__(self, q, tab_index, source_in=None):
        self.q = q
        self.tab_index = tab_index
        self.source_in = source_in

        self.tabs = [
            (*Tabs[0], 'songs', self.show_songs),
            (*Tabs[1], 'albums', self.show_albums),
            (*Tabs[2], 'artists', self.show_artists),
            (*Tabs[3], 'playlists', self.show_playlists),
            (*Tabs[4], 'videos', self.show_videos),
        ]

    async def render(self):
        self.render_tab_bar()

    def render_by_tab_index(self, tab_index):
        search_type = self.tabs[tab_index][1]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {'q': self.q, 'type': search_type.value}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query['source_in'] = source_in
        self._app.browser.goto(page='/search', query=query)


class Body(ScrollArea):
    def fillable_bg_height(self):
        """Implement VFillableBg protocol"""
        view = self.widget()
        assert isinstance(view, View)  # make type chckign happy.
        return view.height() - view.accordion.height()


class View(QFrame, BgTransparentMixin):
    def __init__(self, app, q):
        super().__init__()

        self._app = app

        self.title = LargeHeader(f'搜索“{q}”')
        self.hint = MessageLabel()
        self.accordion = Accordion()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 0, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(30)
        self._layout.addWidget(self.title)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.hint)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.accordion)
        self._layout.addStretch(0)
