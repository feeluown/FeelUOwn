from PyQt5.QtCore import Qt

from .textlist import TextlistModel, TextlistView


class ProvidersModel(TextlistModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._association = {}

    def assoc(self, provider_id, pm):
        self._association[provider_id] = pm
        self.add(provider_id)

    def remove(self, provider_id):
        if not self._association.pop(provider_id, None):
            self.remove(provider_id)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        provider_id = self._items[row]
        provider = self._association[provider_id]
        if role == Qt.DisplayRole:
            return provider.symbol + ' ' + provider.text
        if role == Qt.ToolTipRole:
            return provider.desc
        if role == Qt.UserRole:
            return provider
        return super().data(index, role)


class ProvidersView(TextlistView):
    def __init__(self, parent):
        super().__init__(parent)

        self.setMinimumHeight(80)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        provider = index.data(role=Qt.UserRole)
        provider.clicked.emit()
