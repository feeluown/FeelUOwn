from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QHBoxLayout

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
        self.render_toolbar()

        _, search_type, attrname, show_handler = self.tabs[self.tab_index]

        async def models_g():
            async for result in self._app.library.a_search(
                    self.q, source_in=self.source_in, type_in=search_type):
                if result is not None:
                    for obj in (getattr(result, attrname) or []):
                        yield obj

        show_handler(reader=wrap(models_g()))

    def render_toolbar(self):
        source_in = self.source_in or [p.identifier for p in self._app.library.list()]
        toolbar = SearchProvidersFilter(self._app.library.list())
        toolbar.set_checked_providers(source_in)
        self.set_extra(toolbar)
        toolbar.checked_btn_changed.connect(self.update_source_in)

    def update_source_in(self, source_in):
        self._app.browser.local_storage[KeySourceIn] = ','.join(source_in)

    def render_by_tab_index(self, tab_index):
        search_type = self.tabs[tab_index][1]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {'q': self.q, 'tab_index': tab_index}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query['source_in'] = source_in
        self._app.browser.goto(page='/search', query=query)


class _ProviderCheckBox(QCheckBox):
    def set_identifier(self, identifier):
        self.identifier = identifier  # pylint: disable=W0201


class SearchProvidersFilter(QWidget):
    checked_btn_changed = pyqtSignal(list)

    def __init__(self, providers):
        super().__init__()
        self.providers = providers

        self._btns = []
        self._layout = QHBoxLayout(self)

        for provider in self.providers:
            btn = _ProviderCheckBox(provider.name, self)
            btn.set_identifier(provider.identifier)
            btn.clicked.connect(self.on_btn_clicked)
            self._layout.addWidget(btn)
            self._btns.append(btn)

        # HELP: we add spacing between checkboxes because they
        # will overlay each other on macOS by default. Why?
        self._layout.setSpacing(10)
        self._layout.setContentsMargins(30, 0, 30, 0)
        self._layout.addStretch(0)

    def get_checked_providers(self):
        identifiers = []
        for btn in self._btns:
            if btn.isChecked():
                identifiers.append(btn.identifier)
        return identifiers

    def set_checked_providers(self, providers):
        for provider in providers:
            for btn in self._btns:
                if provider == btn.identifier:
                    btn.setChecked(True)
                    break

    def on_btn_clicked(self, _):
        self.checked_btn_changed.emit(self.get_checked_providers())
