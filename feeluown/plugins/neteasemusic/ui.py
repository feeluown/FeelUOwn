import asyncio
import hashlib
import logging

from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot, QTime
from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QLineEdit, QHeaderView,
                             QMenu, QAction, QAbstractItemView,
                             QTableWidgetItem, QSizePolicy)

from feeluown.libs.widgets.base import FLabel, FFrame, FDialog, FLineEdit, \
    FButton, FScrollArea
from feeluown.libs.widgets.components import MusicTable, LP_GroupItem, ImgLabel
from feeluown.utils import set_alpha, parse_ms

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


class _TagCellWidget(FFrame):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self.setObjectName('tag_cell')

        self.download_tag = FLabel('✓', self)
        self.download_flag = False
        self.download_tag.setObjectName('download_tag')
        self.download_tag.setAlignment(Qt.AlignCenter)

        self.set_theme_style()

        self._layout = QHBoxLayout(self)
        self.setup_ui()

    @property
    def download_label_style(self):
        theme = self._app.theme_manager.current_theme
        background = set_alpha(theme.color7, 50).name(QColor.HexArgb)
        if self.download_flag:
            color = theme.color4.name()
        else:
            color = set_alpha(theme.color7, 30).name(QColor.HexArgb)
        style_str = '''
            #download_tag {{
                color: {0};
                background: {1};
                border-radius: 10px;
            }}
        '''.format(color, background)
        return style_str

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        style_str = style_str + self.download_label_style

        self.setStyleSheet(style_str)

    def set_download_tag(self):
        self.download_flag = True
        self.set_theme_style()

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addSpacing(10)
        self._layout.addWidget(self.download_tag)
        self._layout.addSpacing(10)
        self._layout.addStretch(1)
        self.download_tag.setFixedSize(20, 20)


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
            self.songs.pop(self._context_menu_row)
            self._app.message('删除 %s 成功' % song.title)
        else:
            self._app.message('删除 %s 失败' % song.title, error=True)

    def scroll_to_song(self, song):
        for i, s in enumerate(self.songs):
            if s.mid == song.mid:
                item = self.item(i, 1)
                self.scrollToItem(item)
                self.setCurrentItem(item)
                break

    def set_playlist_id(self, pid):
        self._playlist_id = pid

    def is_playlist(self):
        if self._playlist_id:
            return True
        return False

    def add_item(self, song_model):
        music_item = QTableWidgetItem(song_model.title)
        album_item = QTableWidgetItem(song_model.album_name)
        artist_item = QTableWidgetItem(song_model.artists_name)
        m, s = parse_ms(song_model.length)
        duration = QTime(0, m, s)
        length_item = QTableWidgetItem(duration.toString('mm:ss'))

        row = self.rowCount()
        self.setRowCount(row + 1)
        self.setItem(row, 1, music_item)
        self.setItem(row, 2, artist_item)
        self.setItem(row, 3, album_item)
        self.setItem(row, 4, length_item)
        cell_widget = _TagCellWidget(self._app)
        if NSongModel.local_exists(song_model):
            cell_widget.set_download_tag()
        self.setCellWidget(row, 5, cell_widget)

        self.songs.append(song_model)

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


class CoverImgLabel(ImgLabel):
    def __init__(self, app, parent=None):
        super().__init__(app, parent)

        self._app = app
        self.setFixedWidth(160)
        self.setObjectName('n_album_img_label')
        self.set_theme_style()


class DescriptionLabel(FLabel):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self.setObjectName('n_desc_container')
        self.set_theme_style()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                padding-top: 5px;
                padding-bottom: 5px;
                background: transparent;
                color: {1};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_Space:
            self._preview_dialog = DescriptionPreviewDialog(self._app)
            preview_container = self.parent().parent()
            self._preview_dialog.set_copy(preview_container)
            self._preview_dialog.show()
        else:
            super().keyPressEvent(event)


class DescriptionPreviewDialog(FDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('n_desc_preview_dialog')
        self.desc_container = DescriptionContainer(self._app, self)
        self._container = FFrame(self)
        self._container.setObjectName('n_desc_preview_dialog_container')
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.set_theme_style()
        self._container_layout = QVBoxLayout(self._container)
        self._layout = QVBoxLayout(self)
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                color: {3};
            }}
            #{1} {{
                background: {2};
                border: 5px solid {4};
                border-radius: 5px;
                padding: 3px;
            }}
        '''.format(self.objectName(),
                   self._container.objectName(),
                   theme.background.name(),
                   theme.foreground.name(),
                   theme.random_color().name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

        self._layout.addWidget(self._container)
        self._container_layout.addWidget(self.desc_container)

    def set_copy(self, desc_container):
        self.desc_container.set_html(desc_container.html)

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_Space:
            self.close()
        else:
            super().keyPressEvent(event)


class DescriptionContainer(FScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self._app = app
        self.desc_label = DescriptionLabel(self._app)
        self.setObjectName('n_desc_container')
        self.set_theme_style()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._layout = QVBoxLayout(self)
        self.setWidget(self.desc_label)
        self.setWidgetResizable(True)
        self.setup_ui()

    @property
    def html(self):
        return self.desc_label.text()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                border: 0;
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def set_html(self, desc):
        self.desc_label.setText(desc)
        self.desc_label.setTextFormat(Qt.RichText)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def keyPressEvent(self, event):
        key_code = event.key()
        if key_code == Qt.Key_J:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value + 20)
        elif key_code == Qt.Key_K:
            value = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(value - 20)
        else:
            super().keyPressEvent(event)


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
        self.img_label = CoverImgLabel(self._app)
        self.desc_container = DescriptionContainer(self._app)
        self.info_container = FFrame(parent=self)
        self.table_control = TableControl(self._app)
        self._layout = QVBoxLayout(self)
        self._info_layout = QHBoxLayout(self.info_container)
        self.setup_ui()

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._info_layout.setContentsMargins(0, 0, 0, 0)
        self._info_layout.setSpacing(0)

        self._info_layout.addWidget(self.img_label)
        self._info_layout.addSpacing(20)
        self._info_layout.addWidget(self.desc_container)

        self._layout.addSpacing(10)
        self._layout.addWidget(self.info_container)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.table_control)

    def set_table(self, songs_table):
        if self.songs_table:
            self._layout.replaceWidget(self.songs_table, songs_table)
            self.songs_table.deleteLater()
        else:
            self._layout.addWidget(songs_table)
            self._layout.addSpacing(10)
        self.songs_table = songs_table

    def load_img(self, img_url, img_name):
        self.info_container.show()
        event_loop = asyncio.get_event_loop()
        future = event_loop.create_task(
            self._app.img_ctl.get(img_url, img_name))
        future.add_done_callback(self.set_img)

    def set_img(self, future):
        content = future.result()
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if pixmap.isNull():
            return None
        self.img_label.setPixmap(
            pixmap.scaledToWidth(self.img_label.width(),
                                 mode=Qt.SmoothTransformation))

    def set_desc(self, desc):
        self.desc_container.set_html(desc)

    def hide_info_container(self):
        self.info_container.hide()


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
        self.login_btn.setToolTip('点击可刷新歌单列表')
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
