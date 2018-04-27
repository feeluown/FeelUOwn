from PyQt5.QtCore import (
    QAbstractTableModel,
    Qt,
    QVariant
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class SongsTable(QTableWidget):

    def __init__(self, rows=0, columns=6, parent=None):
        super().__init__(rows, columns, parent)

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        self.horizontalHeader().setDefaultAlignment(self._alignment)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)

        self.setObjectName('music_table')
        self.set_theme_style()
        self.songs = []

        self.setHorizontalHeaderLabels(['', '歌曲名', '歌手', '专辑', '时长',
                                        ''])
        self.setColumnWidth(0, 28)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 150)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 30)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cellDoubleClicked.connect(self.on_cell_dbclick)

    def add_item(self, song_model):
        music_item = QTableWidgetItem(song_model.title)
        album_item = QTableWidgetItem(song_model.album_name)
        artist_item = QTableWidgetItem(song_model.artists_name)
        m, s = parse_ms(song_model.length)
        duration = QTime(0, m, s)
        length_item = QTableWidgetItem(duration.toString())

        row = self.rowCount()
        self.setRowCount(row + 1)
        self.setItem(row, 1, music_item)
        self.setItem(row, 2, artist_item)
        self.setItem(row, 3, album_item)
        self.setItem(row, 4, length_item)

        self.songs.append(song_model)

    def set_songs(self, songs):
        self.setRowCount(0)
        self.songs = []
        for song in songs:
            self.add_item(song)

    def on_cell_dbclick(self, row, column):
        song = self.songs[row]
        if column == 0:
            pass
        elif column == 1:
            self.play_song_signal.emit(song)
        elif column == 2:
            pass
        elif column == 3:
            pass

    def keyPressEvent(self, event):
        self.setFocus()     # gain focus from cell widget if neccesary
        key_code = event.key()
        if key_code == Qt.Key_J:
            self.setCurrentCell(self._next_row(), 1)
        elif key_code == Qt.Key_K:
            self.setCurrentCell(self._prev_row(), 1)
        elif key_code in (Qt.Key_Enter, Qt.Key_Return):
            current_row = self.currentRow()
            self.play_song_signal.emit(self.songs[current_row])
        else:
            super().keyPressEvent(event)

    def _next_row(self):
        current_row = self.currentRow()
        return current_row + 1 if current_row != (self.rowCount() - 1)\
            else current_row

    def _prev_row(self):
        current_row = self.currentRow()
        return current_row - 1 if current_row != 0 else 0
