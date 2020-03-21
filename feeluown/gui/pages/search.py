from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QCheckBox, QHBoxLayout

from fuocore.reader import wrap
from fuocore.models import SearchType
from feeluown.widgets.tabbar import Tab
from feeluown.widgets.magicbox import KeySourceIn, KeyType
from feeluown.containers.table import Renderer


TypeTabMapping = {
    SearchType.so: Tab.songs,
    SearchType.al: Tab.albums,
    SearchType.ar: Tab.artists,
    SearchType.pl: Tab.playlists,
}


async def render(req, **kwargs):
    """/search handler

    :type app: feeluown.app.App
    """
    q = req.query.get('q', '')
    if not q:
        return
    type_ = req.query.get('type', None)
    type_ = SearchType.parse(type_) if type_ else SearchType.so
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None

    app = req.ctx['app']
    ui = app.ui
    right_panel = ui.right_panel
    table_container = right_panel.table_container

    right_panel.collection_container.hide()
    right_panel.scrollarea.show()

    reader = wrap(await app.library.a_search(q, type_in=type_, source_in=source_in))
    renderer = SearchResultRenderer(q, type_, reader, source_in=source_in)
    await table_container.set_renderer(renderer)


class SearchResultRenderer(Renderer):
    def __init__(self, q, type_, reader, source_in=None):
        self.q = q
        self.type_ = type_
        self.source_in = source_in
        self.reader = reader

    async def render(self):
        mapping = {
            SearchType.so: ('songs', self.show_songs,
                            self.tabbar.show_songs_needed),
            SearchType.al: ('albums', self.show_albums,
                            self.tabbar.show_albums_needed),
            SearchType.ar: ('artists', self.show_artists,
                            self.tabbar.show_artists_needed),
            SearchType.pl: ('playlists', self.show_playlists,
                            self.tabbar.show_playlists_needed),
        }
        for search_type, (_, _, signal) in mapping.items():
            signal.connect(self._show(search_type))

        self.tabbar.show()
        self.tabbar.library_mode()
        self.tabbar.check(TypeTabMapping[self.type_])

        self.meta_widget.show()
        self.meta_widget.title = '搜索 “{}”'.format(self.q)

        self.render_toolbar()

        attr, show_handler, signal = mapping[self.type_]
        objects = []
        for result in self.reader:
            objects.extend(getattr(result, attr) or [])
        show_handler(objects)

    def render_toolbar(self):
        source_in = self.source_in or [p.identifier for p in self._app.library.list()]
        toolbar = SearchProvidersFilter(self._app.library.list())
        toolbar.set_checked_providers(source_in)
        self.set_extra(toolbar)
        toolbar.checked_btn_changed.connect(self.update_source_in)

    def update_source_in(self, source_in):
        self._app.browser.local_storage[KeySourceIn] = ','.join(source_in)

    def _show(self, type_):
        def cb():
            self._app.browser.local_storage[KeyType] = type_.value
            query = {'q': self.q, 'type': type_.value}
            source_in = self._app.browser.local_storage.get(KeySourceIn, None)
            if source_in is not None:
                query['source_in'] = source_in
            self._app.browser.goto(uri='/search', query=query)
        return cb


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
