from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel,  QWidget, QCheckBox, \
    QVBoxLayout, QHBoxLayout

from feeluown.gui.widgets.magicbox import KeySourceIn

FILTER_MEDIA_PROVIDER = False
# filter_media_provider = False

class HeaderLabel(QLabel):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = self.font()
        font.setBold(True)
        self.setFont(font)
        self.setText(text)


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

class MediaProvider(SearchProvidersFilter):
    def __init__(self, providers):
        super().__init__(providers)

class SettingsDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setWindowTitle('应用配置')
        self.render()

    def render(self):
        source_in_str = self._app.browser.local_storage.get(KeySourceIn)
        if source_in_str is not None:
            source_in = source_in_str.split(',')
        else:
            source_in = [p.identifier for p in self._app.library.list()]
        toolbar = SearchProvidersFilter(self._app.library.list())
        toolbar.set_checked_providers(source_in)
        toolbar.checked_btn_changed.connect(self.update_source_in)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(HeaderLabel('搜索来源'))
        self._layout.addWidget(toolbar)
        self._layout.addStretch(0)

        global FILTER_MEDIA_PROVIDER
        if FILTER_MEDIA_PROVIDER == False:
            FILTER_MEDIA_PROVIDER = source_in

        toolbar1 = MediaProvider(self._app.library.list())
        toolbar1.set_checked_providers(FILTER_MEDIA_PROVIDER)
        toolbar1.checked_btn_changed.connect(self.update_media_in)

        self._layout.addWidget(HeaderLabel('播放来源'))
        self._layout.addWidget(toolbar1)
        self._layout.addStretch(0)

    def update_source_in(self, source_in):
        self._app.browser.local_storage[KeySourceIn] = ','.join(source_in)

    def update_media_in(self, source_in):
        global FILTER_MEDIA_PROVIDER
        FILTER_MEDIA_PROVIDER = source_in
