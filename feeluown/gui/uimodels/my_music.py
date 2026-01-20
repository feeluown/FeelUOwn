from feeluown.utils.dispatch import Signal
from feeluown.gui.widgets.my_music import MyMusicModel


class MyMusicItem:
    def __init__(self, text):
        self.text = text
        self.clicked = Signal()


class MyMusicUiManager:
    """

    .. note::

    Currently, we use an array data structure to store items,
    only providing add_item and clear methods.
    We want the items in MyMusic to remain associated with the provider.
    The provider is the context of MyMusic.

    And the Provider is a relatively higher-level object;
    we will provide get_item for more fine-grained control.
    """

    def __init__(self, app):
        self._app = app
        self._items = []
        self.model = MyMusicModel(app)

    @classmethod
    def create_item(cls, text):
        return MyMusicItem(text)

    def add_item(self, item):
        self.model.add(item)
        self._items.append(item)

    def clear(self):
        self._items.clear()
        self.model.clear()
