from PyQt5.QtWidgets import QWidget, QHBoxLayout


class StatusLineItem:
    """状态栏组件"""
    def __init__(self, name, widget):
        self.name = name
        self.widget = widget

    def __eq__(self, other):
        return isinstance(other, StatusLineItem) \
            and other.name == self.name \
            and other.widget is self.widget


class StatusLine(QWidget):
    """状态栏（类似 Emacs/Vim status line）"""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._items = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def add_item(self, item):
        """添加组件"""
        if item not in self._items:
            self._items.append(item)
            self._layout.addWidget(item.widget)

    def remove_item(self, item):
        """移除组件

        :param item: 一个 StatusLineItem 对象，或者 item 名字
        """
        pass
