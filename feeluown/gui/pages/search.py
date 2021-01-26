from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QHBoxLayout

from feeluown.utils.reader import wrap
from feeluown.models import SearchType
from feeluown.widgets.tabbar import Tab
from feeluown.widgets.magicbox import KeySourceIn, KeyType
from feeluown.gui.page_containers.table import Renderer
from feeluown.gui.base_renderer import LibraryTabRendererMixin


TabidSearchMapping = {
    Tab.songs: (SearchType.so, 'songs'),
    Tab.albums: (SearchType.al, 'albums'),
    Tab.artists: (SearchType.ar, 'artists'),
    Tab.playlists: (SearchType.pl, 'playlists'),
    Tab.videos: (SearchType.vi, 'videos'),
}


async def render(req, **kwargs):
    """/search handler

    :type app: feeluown.app.App
    """
    q = req.query.get('q', '')
    if not q:
        return
    tab_id = Tab(int(req.query.get('tab_id', Tab.songs.value)))
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None

    app = req.ctx['app']
    ui = app.ui
    right_panel = ui.right_panel
    table_container = right_panel.table_container
    right_panel.set_body(right_panel.scrollarea)

    search_type, _ = TabidSearchMapping[tab_id]
    reader = wrap(app.library.a_search(q, source_in=source_in, type_in=search_type))
    renderer = SearchResultRenderer(q, tab_id, reader, source_in=source_in)
    await table_container.set_renderer(renderer)


class SearchResultRenderer(Renderer, LibraryTabRendererMixin):
    def __init__(self, q, tab_id, reader, source_in=None):
        self.q = q
        self.tab_id = tab_id
        self.source_in = source_in
        self.reader = reader

    async def render(self):
        self.init_tabbar_signal_binding()

        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(self.tab_id)

        self.meta_widget.show()
        self.meta_widget.title = '搜索 “{}”'.format(self.q)

        self.render_toolbar()

        show_handler = self.get_tabid_handler_mapping()[self.tab_id]
        _, attrname = TabidSearchMapping[self.tab_id]

        async def models_g():
            async for result in self.reader:
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

    def show_by_tab_id(self, tab_id):
        search_type = TabidSearchMapping[tab_id][0]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {'q': self.q, 'tab_id': tab_id.value}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query['source_in'] = source_in
        self._app.browser.goto(page='/search', query=query)


class _ProviderCheckBox(QCheckBox):
    def set_identifier(self, identifier):
        self.identifier = identifier


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
