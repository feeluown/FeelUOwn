"""
FIXME: 感觉这个 component 设计有点问题，做的事情太多，得拆！
"""

from PyQt5.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QSize,
    Qt,
    QVariant,
)
from PyQt5.QtWidgets import (
    QListView,
    QSizePolicy,
)


class ProviderModel(object):
    """
    一个 ProviderModel 对应左边栏「我的音乐」下的一个项目

    FIXME: 或许不应该命名为 ProviderModel，而是
    """
    def __init__(self, name, icon='♬ ', desc='', on_click=None, **kwargs):
        self.name = name
        self.icon = icon
        self.desc = desc
        self._on_click = on_click


class ProvidersModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._provider_list = []
        self._association = {}

    def assoc(self, provider_id, pm):
        self._association[provider_id] = pm
        self._provider_list.append(provider_id)
        self.insertRow(len(self._provider_list))

    def get(self, provider_id):
        return self._association.get(provider_id)

    def remove(self, provider_id):
        if not self._association.pop(provider_id, None):
            row = self._provider_list.index(provider_id)
            self._provider_list.remove(provider_id)
            self.removeRow(row)

    def rowCount(self, parent=QModelIndex()):
        return len(self._provider_list)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        if row >= len(self._provider_list) or row < 0:
            return QVariant()

        provider_id = self._provider_list[row]
        provider = self._association[provider_id]
        if role == Qt.DisplayRole:
            return provider.icon + ' ' + provider.name
        elif role == Qt.ToolTipRole:
            return provider.desc
        elif role == Qt.UserRole:
            return provider
        return QVariant()


class ProvidersView(QListView):
    def __init__(self, parent):
        super().__init__(parent)

        self.setMinimumHeight(80)
        self.setAttribute(Qt.WA_MacShowFocusRect, 0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self, index):
        provider = index.data(role=Qt.UserRole)
        if provider._on_click:
            provider._on_click()

    def sizeHint(self):
        height = 10
        if self.model().rowCount() > 0:
            height = self.model().rowCount() * self.sizeHintForRow(0)
        return QSize(self.width(), height)
