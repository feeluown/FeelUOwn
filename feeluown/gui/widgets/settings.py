from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QWidget, QCheckBox, \
    QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton

from feeluown.gui.widgets.magicbox import KeySourceIn
from feeluown.gui.widgets.header import MidHeader
from feeluown.gui.components import LyricButton, WatchButton


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


class PlayerSettings(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self.lyric_btn = LyricButton(app, height=16)
        self.watch_btn = WatchButton(app, height=16)
        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self.lyric_btn)
        self._layout.addWidget(self.watch_btn)
        self._layout.addStretch(0)


class AISettings(QWidget):
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._app = app
        self._prompt_editor = QPlainTextEdit(self)
        self._save_btn = QPushButton('保存', self)

        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self._prompt_editor)
        self._layout.addWidget(self._save_btn)
        self._prompt_editor.setPlainText(self._app.config.AI_RADIO_PROMPT)
        self._prompt_editor.setMaximumHeight(200)

        self._save_btn.clicked.connect(self.save_prompt)

    def save_prompt(self):
        self._app.config.AI_RADIO_PROMPT = self._prompt_editor.toPlainText()


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
        self._layout.addWidget(MidHeader('搜索来源'))
        self._layout.addWidget(toolbar)
        self._layout.addWidget(MidHeader('AI 电台（PROMPT）'))
        self._layout.addWidget(AISettings(self._app))
        self._layout.addWidget(MidHeader('播放器'))
        self._layout.addWidget(PlayerSettings(self._app))
        self._layout.addStretch(0)

    def update_source_in(self, source_in):
        self._app.browser.local_storage[KeySourceIn] = ','.join(source_in)
