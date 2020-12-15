from feeluown.utils.dispatch import Signal
from feeluown.widgets.my_music import MyMusicModel


class MyMusicItem(object):
    def __init__(self, text):
        self.text = text
        self.clicked = Signal()


class MyMusicUiManager:
    """

    .. note::

        目前，我们用数组的数据结构来保存 items，只提供 add_item 和 clear 方法。
        我们希望，MyMusic 中的 items 应该和 provider 保持关联。provider 是 MyMusic
        的上下文。

        而 Provider 是比较上层的对象，我们会提供 get_item 这种比较精细的控制方法。
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
