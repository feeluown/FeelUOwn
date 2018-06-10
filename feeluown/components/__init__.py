from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
    QTime,
    QVariant,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QTableView,
)


class SongsTable(QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)

        # self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # self.verticalHeader().hide()
        # self.setShowGrid(False)
        # self.setAlternatingRowColors(True)
        # self.setColumnWidth(0, 28)
        # self.setColumnWidth(2, 150)
        # self.setColumnWidth(3, 150)
        # self.setColumnWidth(4, 50)
        # self.setColumnWidth(5, 30)
        # self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # def keyPressEvent(self, event):
    #     self.setFocus()     # gain focus from cell widget if neccesary
    #     key_code = event.key()
    #     if key_code == Qt.Key_J:
    #         self.setCurrentCell(self._next_row(), 1)
    #     elif key_code == Qt.Key_K:
    #         self.setCurrentCell(self._prev_row(), 1)
    #     elif key_code in (Qt.Key_Enter, Qt.Key_Return):
    #         current_row = self.currentRow()
    #     else:
    #         super().keyPressEvent(event)

    def _next_row(self):
        current_row = self.currentRow()
        return current_row + 1 if current_row != (self.rowCount() - 1)\
            else current_row

    def _prev_row(self):
        current_row = self.currentRow()
        return current_row - 1 if current_row != 0 else 0
