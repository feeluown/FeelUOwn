from feeluown.widgets.provider import ProvidersModel

from feeluown.utils.dispatch import Signal


class ProviderUiItem:
    """(alpha)

    **关于 clicked 信号**

    之前在设计 ProviderUiItem 的时候，我们是在构造函数中传入一个 on_click
    参数，当时就觉得这样的代码写起来有点奇怪：“传入一个函数来做为 callback”，
    现在算是找到一个解决方案了。
    """

    def __init__(self, name, text, symbol, desc):
        # 如果需要，可以支持右键弹出菜单
        self._name = name
        self.text = text
        self.symbol = symbol
        self.desc = desc
        self.clicked = Signal()

    @property
    def name(self):
        return self._name


class ProviderUiManager:
    """(alpha)"""

    def __init__(self, app):
        self._app = app
        # name:model mapping
        self._items = {}
        self.model = ProvidersModel(self._app)

    @classmethod
    def create_item(self, name, text, symbol='♬ ', desc=''):
        return ProviderUiItem(name, text, symbol, desc)

    def get_item(self, name):
        return self._items.get(name)

    def add_item(self, uiitem):
        name = uiitem.name
        self.model.assoc(name, uiitem)
        self._items[name] = uiitem
        return True

    def remove_item(self, uiitem):
        if isinstance(uiitem, ProviderUiItem):
            name = uiitem.name
        else:
            name = uiitem
        if name in self._items:
            self.model.remove(name)
            self._items.remove(name)
            return True
        return False
