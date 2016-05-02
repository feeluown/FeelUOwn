import hashlib
import logging

from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView,\
    QTableWidgetItem

from feeluown.libs.widgets.base import FLabel, FFrame, FDialog, FLineEdit, \
    FButton
from feeluown.libs.widgets.components import MusicTable, LP_GroupItem
from feeluown.utils import parse_ms, lighter, darker

from .model import NPlaylistModel, NSongModel


logger = logging.getLogger(__name__)


class LineInput(FLineEdit):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('line_input')
        self.set_theme_style()

    def set_theme_style(self):
        pass


class LoginDialog(FDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.is_encrypted = False
        self.captcha_needed = False
        self.captcha_id = 0

        self.username_input = LineInput(self)
        self.pw_input = LineInput(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        # self.remember_checkbox = FCheckBox(self)
        self.captcha_label = FLabel(self)
        self.captcha_label.hide()
        self.captcha_input = LineInput(self)
        self.captcha_input.hide()
        self.hint_label = FLabel(self)
        self.ok_btn = FButton('登录', self)
        self._layout = QVBoxLayout(self)

        self.username_input.setPlaceholderText('网易邮箱或者手机号')
        self.pw_input.setPlaceholderText('密码')

        self.setObjectName('login_dialog')
        self.set_theme_style()
        self.setup_ui()

        self.pw_input.textChanged.connect(self.dis_encrypt)

    def fill(self, data):
        self.username_input.setText(data['username'])
        self.pw_input.setText(data['password'])
        self.is_encrypted = True

    def set_theme_style(self):
        pass

    def setup_ui(self):
        self.setFixedWidth(200)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.username_input)
        self._layout.addWidget(self.pw_input)
        self._layout.addWidget(self.captcha_label)
        self._layout.addWidget(self.captcha_input)
        self._layout.addWidget(self.hint_label)
        # self._layout.addWidget(self.remember_checkbox)
        self._layout.addWidget(self.ok_btn)

    def show_hint(self, text):
        self.hint_label.setText(text)

    @property
    def data(self):
        username = self.username_input.text()
        pw = self.pw_input.text()
        if self.is_encrypted:
            password = pw
        else:
            password = hashlib.md5(pw.encode('utf-8')).hexdigest()
        d = dict(username=username, password=password)
        return d

    def captcha_verify(self, data):
        self.captcha_needed = True
        url = data['captcha_url']
        self.captcha_id = data['captcha_id']
        self.captcha_input.show()
        self.captcha_label.show()
        self._app.pixmap_from_url(url, self.captcha_label.setPixmap)

    def dis_encrypt(self, text):
        self.is_encrypted = False


class LoginButton(FLabel):
    clicked = pyqtSignal()

    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setText('登录')
        self.setToolTip('登陆网易云音乐')
        self.setObjectName('n_login_btn')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color4.name())
        self.setStyleSheet(style_str)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_avatar(self, url):
        pixmap = self._app.pixmap_from_url(url)
        if pixmap is not None:
            self.setPixmap(pixmap.scaled(self.size(),
                           transformMode=Qt.SmoothTransformation))


class PlaylistItem(LP_GroupItem):
    load_playlist_signal = pyqtSignal(NPlaylistModel)

    def __init__(self, app, playlist=None, parent=None):
        super().__init__(app, playlist.name, parent=parent)

        self.model = playlist
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        self.load_playlist_signal.emit(self.model)


class SongsTable(MusicTable):
    play_mv_signal = pyqtSignal([int])
    play_song_signal = pyqtSignal([NSongModel])
    show_artist_signal = pyqtSignal([int])
    show_album_signal = pyqtSignal([int])

    def __init__(self, app, rows=0, columns=6, parent=None):
        super().__init__(app, rows, columns, parent)
        self._app = app

        self.setObjectName('nem_songs_table')
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

    def on_cell_dbclick(self, row, column):
        song = self.songs[row]
        if column == 0:
            if NSongModel.mv_available(song.mvid):
                self.play_mv_signal.emit(song.mvid)
        elif column == 1:
            self.play_song_signal.emit(self.songs[row])
        elif column == 2:
            self.show_artist_signal.emit(song.artists[0].aid)
        elif column == 3:
            self.show_album_signal.emit(song.album.bid)


class SearchBox(FLineEdit):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('search_box')
        self.setPlaceholderText('搜索歌曲、歌手')
        self.setToolTip('输入文字可以从当前歌单内搜索'
                        '按下 Enter 将搜索网络')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                padding-left: 3px;
                font-size: 14px;
                background: transparent;
                border: 0px;
                border-bottom: 1px solid {1};
                color: {2};
                outline: none;
            }}
            #{0}:focus {{
                outline: none;
            }}
        '''.format(self.objectName(),
                   theme.color6.name(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)


class TableControl(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.play_all_btn = FButton('▶')
        self.search_box = SearchBox(self._app)
        self._layout = QHBoxLayout(self)
        self.setup_ui()
        self.setObjectName('n_table_control')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            QPushButton {{
                background: transparent;
                color: {1};
                font-size: 16px;
                outline: none;
            }}
            QPushButton:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setFixedHeight(40)
        self.play_all_btn.setFixedSize(20, 20)
        self.search_box.setFixedSize(160, 26)

        self._layout.addSpacing(20)
        self._layout.addWidget(self.play_all_btn)
        self._layout.addStretch(0)
        self._layout.addWidget(self.search_box)
        self._layout.addSpacing(60)


class SongsTable_Container(FFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.songs_table = None
        self.table_control = TableControl(self._app)
        self._layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.table_control)

    def set_table(self, songs_table):
        if self.songs_table:
            self._layout.replaceWidget(self.songs_table, songs_table)
            self.songs_table.close()
            del self.songs_table
        else:
            self._layout.addWidget(songs_table)
            self._layout.addSpacing(10)
        self.songs_table = songs_table


class Ui(object):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.login_dialog = LoginDialog(self._app, self._app)
        self.login_btn = LoginButton(self._app)
        self._lb_container = FFrame()
        self.songs_table_container = SongsTable_Container(self._app)

        self._lbc_layout = QHBoxLayout(self._lb_container)

        self.setup()

    def setup(self):

        self._lbc_layout.setContentsMargins(0, 0, 0, 0)
        self._lbc_layout.setSpacing(0)

        self._lbc_layout.addWidget(self.login_btn)
        self.login_btn.setFixedSize(30, 30)
        self._lbc_layout.addSpacing(10)

        tp_layout = self._app.ui.top_panel.layout()
        tp_layout.addWidget(self._lb_container)
