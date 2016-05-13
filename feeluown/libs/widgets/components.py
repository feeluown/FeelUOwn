# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout, QAbstractItemView, QHeaderView, \
    QTableWidgetItem

from .base import FFrame, FLabel, FTableWidget
from feeluown.model import SongModel
from feeluown.utils import darker, parse_ms, measure_time


class LP_GroupHeader(FFrame):
    def __init__(self, app, title=None, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.title_label = FLabel(title, self)
        self.title_label.setIndent(8)

        self.setObjectName('lp_group_header')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}

            #{0} QLabel {{
                font-size: 12px;
                color: {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(22)

        self._layout.addWidget(self.title_label)

    def set_header(self, text):
        self.title_label.setText(text)


class LP_GroupItem(FFrame):
    clicked = pyqtSignal()

    def __init__(self, app, name=None, parent=None):
        super().__init__(parent)
        self._app = app

        self.is_selected = False
        self.is_playing = False

        self._layout = QHBoxLayout(self)
        self._flag_label = FLabel(self)
        self._img_label = FLabel(self)
        self._name_label = FLabel(name, self)

        self.setObjectName('lp_group_item')
        self._flag_label.setObjectName('lp_groun_item_flag')
        self._flag_label.setText('➣')
        self._flag_label.setIndent(5)
        self._img_label.setObjectName('lp_group_item_img')
        self._img_label.setText('♬')
        self._name_label.setObjectName('lp_group_item_name')
        self.set_theme_style()
        self.setup_ui()

    def set_img_text(self, text):
        self._img_label.setText(text)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()

    def enterEvent(self, event):
        theme = self._app.theme_manager.current_theme
        label_hover_color = theme.color4
        if self.is_selected or self.is_playing:
            return
        self._img_label.setStyleSheet(
            'color: {0};'.format(label_hover_color.name()))
        self._name_label.setStyleSheet(
            'color: {0};'.format(label_hover_color.name()))

    def leaveEvent(self, event):
        theme = self._app.theme_manager.current_theme
        label_color = theme.foreground
        if self.is_selected or self.is_playing:
            return
        self._img_label.setStyleSheet('color: {0};'.format(label_color.name()))
        self._name_label.setStyleSheet('color: {0};'.format(label_color.name()))

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
            #{1} {{
                color: transparent;
                font-size: 14px;
            }}
            #{2} {{
                color: {4};
                font-size: 14px;
            }}
            #{3} {{
                color: {4};
                font-size: 13px;
            }}
        '''.format(self.objectName(),
                   self._flag_label.objectName(),
                   self._img_label.objectName(),
                   self._name_label.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(26)
        self._img_label.setFixedWidth(18)
        self._flag_label.setFixedWidth(22)

        self._layout.addWidget(self._flag_label)
        self._layout.addWidget(self._img_label)
        self._layout.addSpacing(2)
        self._layout.addWidget(self._name_label)

    def set_selected(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
            #{1} {{
                color: {4};
                font-size: 14px;
            }}
            #{2} {{
                color: {5};
                font-size: 14px;
            }}
            #{3} {{
                color: {6};
                font-size: 13px;
            }}
        '''.format(self.objectName(),
                   self._flag_label.objectName(),
                   self._img_label.objectName(),
                   self._name_label.objectName(),
                   theme.color5_light.name(),
                   theme.color6.name(),
                   theme.color3_light.name())
        self.setStyleSheet(style_str)


class MusicTable(FTableWidget):
    play_song_signal = pyqtSignal([SongModel])

    def __init__(self, app, rows=0, columns=6, parent=None):
        super().__init__(rows, columns, parent)
        self._app = app

        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._alignment = Qt.AlignLeft | Qt.AlignVCenter
        self.horizontalHeader().setDefaultAlignment(self._alignment)
        self.verticalHeader().hide()
        self.setShowGrid(False)

        self.setObjectName('music_table')
        self.set_theme_style()
        self.songs = []

        self.setHorizontalHeaderLabels(['', '歌曲名', '歌手', '专辑', '时长',
                                        ''])
        self.setColumnWidth(0, 28)
        self.setColumnWidth(2, 150)
        self.setColumnWidth(3, 200)
        self.setColumnWidth(5, 100)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cellDoubleClicked.connect(self.on_cell_dbclick)

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            QHeaderView {{
                color: {1};
                background: transparent;
                font-size: 14px;
            }}
            QHeaderView::section:horizontal {{
                height: 24px;
                background: transparent;
                border-top: 1px;
                border-right: 1px;
                border-bottom: 1px;
                border-color: {5};
                color: {5};
                border-style: solid;
                padding-left: 5px;
            }}

            QTableView QTableCornerButton::section {{
                background: transparent;
                border: 0px;
                border-bottom: 1px solid {1};
            }}
            #{0} {{
                border: 0px;
                background: transparent;
                color: {1};
            }}
            #{0}::item {{
                outline: none;
            }}
            #{0}::item:focus {{
                background: transparent;
                outline: none;
            }}
            #{0}::item:selected {{
                background: {4};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color6.name(),
                   darker(theme.background, a=50).name(QColor.HexArgb),
                   theme.color0.name(),
                   theme.color7_light.name())
        self.setStyleSheet(style_str)

    def add_item(self, song_model):
        music_item = QTableWidgetItem(song_model.title)
        album_item = QTableWidgetItem(song_model.album_name)
        artist_item = QTableWidgetItem(song_model.artists_name)
        m, s = parse_ms(song_model.length)
        length_item = QTableWidgetItem(str(m) + ':' + str(s))

        row = self.rowCount()
        self.setRowCount(row + 1)
        self.setItem(row, 1, music_item)
        self.setItem(row, 2, artist_item)
        self.setItem(row, 3, album_item)
        self.setItem(row, 4, length_item)

        self.songs.append(song_model)

    def set_songs(self, songs):
        self.setRowCount(0)
        for song in songs:
            self.add_item(song)

    @measure_time
    def search(self, text):
        if not text:
            for i in range(self.rowCount()):
                self.showRow(i)
            return
        for i, song in enumerate(self.songs):
            if text.lower() not in song.title.lower()\
                    and text not in song.album_name.lower()\
                    and text not in song.artists_name.lower():
                self.hideRow(i)
            else:
                self.showRow(i)

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
        return current_row + 1 if current_row != (self.rowCount() - 1) else 0

    def _prev_row(self):
        current_row = self.currentRow()
        return current_row - 1 if current_row != 0 else self.rowCount() - 1
