"""
FIXME: 感觉这个 component 设计有点问题，做的事情太多，得拆！
"""

from PyQt5.QtCore import Qt, QModelIndex

from .textlist import TextlistModel, TextlistView


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


class ProvidersModel(TextlistModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._association = {}

    def assoc(self, provider_id, pm):
        self._association[provider_id] = pm
        self.add(provider_id)

    def get(self, provider_id):
        return self._association.get(provider_id)

    def remove(self, provider_id):
        if not self._association.pop(provider_id, None):
            self.remove(provider_id)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        provider_id = self._items[row]
        provider = self._association[provider_id]
        if role == Qt.DisplayRole:
            return provider.icon + ' ' + provider.name
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
        if provider._on_click:
            provider._on_click()
