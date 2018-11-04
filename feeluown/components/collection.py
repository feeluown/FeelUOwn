from PyQt5.QtCore import (
    pyqtSignal,
    Qt,
)
from PyQt5.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QAbstractItemView,
    QHeaderView,
)


class CollectionItemsTable(QTableWidget):
    show_url = pyqtSignal([str])

    def __init__(self, parent):
        super().__init__(0, 2, parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setHorizontalHeaderLabels(['地址', '描述'])
        self._setup_ui()

        self._items = []
        self.cellDoubleClicked.connect(
            lambda row, col: self.show_url.emit(self._items[row][0]))

    def _setup_ui(self):
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setColumnWidth(0, 300)

    def show_items(self, items):
        self.setRowCount(0)
        self._items = []
        for index, item in enumerate(items):
            row = index
            url, desc = item
            self.setRowCount(row + 1)
            url_item = QTableWidgetItem(url)
            desc_item = QTableWidgetItem(desc)
            self.setItem(row, 0, url_item)
            self.setItem(row, 1, desc_item)
        self._items = items
