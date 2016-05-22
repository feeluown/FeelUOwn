import hashlib
import logging

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView,
                             QMenu, QAction, QAbstractItemView)

from feeluown.libs.widgets.base import FLabel, FFrame, FDialog, FLineEdit, \
    FButton
from feeluown.libs.widgets.components import MusicTable, LP_GroupItem

from .model import NPlaylistModel, NSongModel, NUserModel


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
        self.setObjectName('nem_login_btn')
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()

    def set_avatar(self, url):
        pixmap = self._app.pixmap_from_url(url)
        if pixmap is not None:
            self.setPixmap(pixmap.scaled(self.size(),
                           transformMode=Qt.SmoothTransformation))


class PlaylistItem(LP_GroupItem):
    load_playlist_signal = pyqtSignal(NPlaylistModel)
    pids = []

    def __init__(self, app, playlist=None, parent=None):
        super().__init__(app, playlist.name, parent=parent)
        self._app = app
        self.existed = False
        if playlist.pid in PlaylistItem.pids:
            self.existed = True
        PlaylistItem.pids.append(playlist.pid)

        self.model = playlist
        self.clicked.connect(self.on_clicked)
        self.setAcceptDrops(True)

    def on_clicked(self):
        self.load_playlist_signal.emit(self.model)

    def dropEvent(self, event):
        source = event.source()
        if not isinstance(source, SongsTable):
            return
        event.accept()
        song = source.drag_song
        if song is not None:
            user = NUserModel.current_user
            if user.is_playlist_mine(self.model.pid):
                self.add_song_to_playlist(song)

    def add_song_to_playlist(self, song):
        logger.debug('temp to add "%s" to playlist "%s"' %
                     (song.title, self.model.name))
        if self.model.add_song(song.mid):
            self._app.message('add "%s" to playlist "%s" success' %
                              (song.title, self.model.name))
        else:
            self._app.message('add "%s" to playlist "%s" failed' %
                              (song.title, self.model.name), error=True)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()


class SongsTable(MusicTable):
    play_mv_signal = pyqtSignal([int])
    play_song_signal = pyqtSignal([NSongModel])
    download_song_signal = pyqtSignal([NSongModel])
    show_artist_signal = pyqtSignal([int])
    show_album_signal = pyqtSignal([int])
    add_song_signal = pyqtSignal([NSongModel])
    set_to_next_signal = pyqtSignal([NSongModel])

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

        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)

        self._context_menu_row = 0
        self._drag_row = None
        self._playlist_id = 0

    @pyqtSlot()
    def add_song_to_current_playlist(self):
        '''do not call explicit, just a slot function'''
        song = self.songs[self._context_menu_row]
        self.add_song_signal.emit(song)

    @pyqtSlot()
    def set_song_to_next(self):
        '''do not call explicit, just a slot function'''
        song = self.songs[self._context_menu_row]
        self.set_to_next_signal.emit(song)

    @pyqtSlot()
    def download_song(self):
        '''do not call explicit, just a slot function'''
        song = self.songs[self._context_menu_row]
        self.download_song_signal.emit(song)

    @pyqtSlot()
    def remove_song_from_playlist(self):
        '''do not call explicit, just a slot function'''
        song = self.songs[self._context_menu_row]
        if NPlaylistModel.del_song_from_playlist(song.mid, self._playlist_id):
            self.removeRow(self._context_menu_row)
            self._app.message('删除 %s 成功' % song.title)
        else:
            self._app.message('删除 %s 失败' % song.title, error=True)

    def set_playlist_id(self, pid):
        self._playlist_id = pid

    def is_playlist(self):
        if self._playlist_id:
            return True
        return False

    def _is_playlist_mine(self):
        if self.is_playlist():
            user = NUserModel.current_user
            if user.is_playlist_mine(self._playlist_id):
                return True
        return False

    def contextMenuEvent(self, event):
        menu = QMenu()
        add_to_current_playlist_action = QAction('添加到当前播放列表', self)
        set_song_next_to_action = QAction('下一首播放', self)
        download_song_action = QAction('下载该歌曲', self)
        menu.addAction(add_to_current_playlist_action)
        menu.addAction(set_song_next_to_action)
        menu.addAction(download_song_action)

        if self._is_playlist_mine():
            remove_song_from_playlist_action = QAction('从歌单中删除该歌曲', self)
            menu.addAction(remove_song_from_playlist_action)
            remove_song_from_playlist_action.triggered.connect(
                self.remove_song_from_playlist)

        add_to_current_playlist_action.triggered.connect(
            self.add_song_to_current_playlist)
        set_song_next_to_action.triggered.connect(
            self.set_song_to_next)
        download_song_action.triggered.connect(self.download_song)

        point = event.pos()
        item = self.itemAt(point)
        if item is not None:
            row = self.row(item)
            self._context_menu_row = row
            menu.exec(event.globalPos())

    @property
    def drag_song(self):
        if self._drag_row is not None:
            return self.songs[self._drag_row]
        return None

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        point = event.pos()
        item = self.itemAt(point)
        if item is not None:
            self._drag_row = self.row(item)

    def on_cell_dbclick(self, row, column):
        song = self.songs[row]
        if column == 0:
            if NSongModel.mv_available(song.mvid):
                self.play_mv_signal.emit(song.mvid)
        elif column == 1:
            self.play_song_signal.emit(song)
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
        self.setToolTip('输入文字可以从当前歌单内搜索\n'
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
            self.songs_table.deleteLater()
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
        self.fm_item = LP_GroupItem(self._app, '私人FM')
        self.fm_item.set_img_text('Ω')
        self.recommend_item = LP_GroupItem(self._app, '每日推荐')
        self.recommend_item.set_img_text('✦')
        self.simi_item = LP_GroupItem(self._app, '相似歌曲')
        self.simi_item.set_img_text('∾')

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

    def on_login_in(self):
        if self.login_dialog.isVisible():
            self.login_dialog.hide()
        library_panel = self._app.ui.central_panel.left_panel.library_panel
        library_panel.add_item(self.fm_item)
        library_panel.add_item(self.simi_item)
        self.hide_simi_item()
        library_panel.add_item(self.recommend_item)

    def show_simi_item(self):
        self.simi_item.show()

    def hide_simi_item(self):
        self.simi_item.hide()
