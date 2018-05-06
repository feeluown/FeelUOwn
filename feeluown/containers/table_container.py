import asyncio

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
)

from feeluown.components.songs import SongsTableModel, SongsTableView


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName('search_box')
        self.setPlaceholderText('搜索歌曲、歌手')
        self.setToolTip('输入文字可以从当前歌单内搜索\n'
                        '按下 Enter 将搜索网络')


class TableControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.play_all_btn = QPushButton('☊', self)
        self.search_box = SearchBox(self)
        self._layout = QHBoxLayout(self)
        self.setup_ui()

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

# class DescriptionLabel(FLabel):
#     def __init__(self, app, parent=None):
#         super().__init__(parent)
#
#         self._app = app
#         self.setObjectName('n_desc_container')
#         self.set_theme_style()
#         self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
#         self.setWordWrap(True)
#         self.setTextInteractionFlags(Qt.TextSelectableByMouse)
#
#     def set_theme_style(self):
#         theme = self._app.theme_manager.current_theme
#         style_str = '''
#             #{0} {{
#                 padding-top: 5px;
#                 padding-bottom: 5px;
#                 background: transparent;
#                 color: {1};
#             }}
#         '''.format(self.objectName(),
#                    theme.foreground.name(),
#                    theme.color0.name())
#         self.setStyleSheet(style_str)
#
#     def keyPressEvent(self, event):
#         key_code = event.key()
#         if key_code == Qt.Key_Space:
#             self._preview_dialog = DescriptionPreviewDialog(self._app)
#             preview_container = self.parent().parent()
#             self._preview_dialog.set_copy(preview_container)
#             self._preview_dialog.show()
#         else:
#             super().keyPressEvent(event)
#
#
#
# class DescriptionPreviewDialog(FDialog):
#     def __init__(self, app, parent=None):
#         super().__init__(parent)
#         self._app = app
#
#         self.setObjectName('n_desc_preview_dialog')
#         self.desc_container = DescriptionContainer(self._app, self)
#         self._container = FFrame(self)
#         self._container.setObjectName('n_desc_preview_dialog_container')
#         self.setWindowFlags(Qt.FramelessWindowHint)
#         self.setAttribute(Qt.WA_TranslucentBackground)
#
#         self.set_theme_style()
#         self._container_layout = QVBoxLayout(self._container)
#         self._layout = QVBoxLayout(self)
#         self.setup_ui()
#
#     def set_theme_style(self):
#         theme = self._app.theme_manager.current_theme
#         style_str = '''
#             #{0} {{
#                 color: {3};
#             }}
#             #{1} {{
#                 background: {2};
#                 border: 5px solid {4};
#                 border-radius: 5px;
#                 padding: 3px;
#             }}
#         '''.format(self.objectName(),
#                    self._container.objectName(),
#                    theme.background.name(),
#                    theme.foreground.name(),
#                    theme.random_color().name())
#         self.setStyleSheet(style_str)
#
#     def setup_ui(self):
#         self._layout.setContentsMargins(0, 0, 0, 0)
#         self._layout.setSpacing(0)
#
#         self._container_layout.setContentsMargins(0, 0, 0, 0)
#         self._container_layout.setSpacing(0)
#
#         self._layout.addWidget(self._container)
#         # self._container_layout.addWidget(self.desc_container)
#
#     def set_copy(self, desc_container):
#         self.desc_container.set_html(desc_container.html)
#
#     def keyPressEvent(self, event):
#         key_code = event.key()
#         if key_code == Qt.Key_Space:
#             self.close()
#         else:
#             super().keyPressEvent(event)
#
#
# class DescriptionContainer(FScrollArea):
#     def __init__(self, app, parent=None):
#         super().__init__(parent)
#
#         self._app = app
#         self.desc_label = DescriptionLabel(self._app)
#         self.setObjectName('n_desc_container')
#         self.set_theme_style()
#
#         self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
#         self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
#         self._layout = QVBoxLayout(self)
#         self.setWidget(self.desc_label)
#         self.setWidgetResizable(True)
#         self.setup_ui()
#
#     @property
#     def html(self):
#         return self.desc_label.text()
#
#     def set_theme_style(self):
#         theme = self._app.theme_manager.current_theme
#         style_str = '''
#             #{0} {{
#                 border: 0;
#                 background: transparent;
#             }}
#         '''.format(self.objectName(),
#                    theme.foreground.name(),
#                    theme.color0.name())
#         self.setStyleSheet(style_str)
#
#     def set_html(self, desc):
#         self.desc_label.setText(desc)
#         self.desc_label.setTextFormat(Qt.RichText)
#
#     def setup_ui(self):
#         self._layout.setContentsMargins(0, 0, 0, 0)
#         self._layout.setSpacing(0)
#
#     def keyPressEvent(self, event):
#         key_code = event.key()
#         if key_code == Qt.Key_J:
#             value = self.verticalScrollBar().value()
#             self.verticalScrollBar().setValue(value + 20)
#         elif key_code == Qt.Key_K:
#             value = self.verticalScrollBar().value()
#             self.verticalScrollBar().setValue(value - 20)
#         else:
#             super().keyPressEvent(event)


class TableOverview(QFrame):
    def __init__(self, parent):
        super().__init__(parent)

        self.cover_label = QLabel(self)
        self.cover_label.setFixedWidth(160)
        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self.cover_label)
        self._layout.addStretch(1)

    def set_cover(self, pixmap):
        self.cover_label.setPixmap(
            pixmap.scaledToWidth(self.cover_label.width(),
                                 mode=Qt.SmoothTransformation))


class SongsTableContainer(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.songs_table = None
        self.table_overview = TableOverview(self)
        self.table_control = TableControl(self._app)
        self._layout = QVBoxLayout(self)
        self.setup_ui()

        self.table_control.play_all_btn.clicked.connect(
            self.play_all)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.table_overview)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.table_control)

    def set_table(self, songs_table):
        songs_table.play_song_needed.connect(self.play_song)
        theme = self._app.theme_manager.current_theme
        if self.songs_table is not None:
            assert self._layout.indexOf(self.songs_table) != -1
            self._layout.replaceWidget(self.songs_table, songs_table)
            self.songs_table.deleteLater()
            songs_table.show()
        else:
            self._layout.addWidget(songs_table)
            self._layout.addSpacing(10)
        self.songs_table = songs_table
        songs_table.show_artist_needed.connect(self.show_artist)

    def play_song(self, song):
        self._app.player.play_song(song)

    def play_all(self):
        songs = self.songs_table.model().songs
        self._app.player.playlist.clear()
        for song in songs:
            self._app.player.playlist.add(song)
        self._app.player.playlist.play_next()

    def show_playlist(self, playlist):
        songs_table_view = SongsTableView(self)
        songs_table_view.setModel(SongsTableModel(playlist.songs))
        self.set_table(songs_table_view)
        if playlist.cover:
            event_loop = asyncio.get_event_loop()
            event_loop.create_task(self.show_cover(playlist.cover))
        self.songs_table.scrollToTop()

    def show_artist(self, artist):
        self.songs_table.setModel(SongsTableModel(artist.songs))
        self.songs_table.scrollToTop()

    async def show_cover(self, cover):
        # FIXME: cover_hash may not work properly someday
        cover_uid = cover.split('/', -1)[-1]
        content = await self._app.img_ctl.get(cover, cover_uid)
        img = QImage()
        img.loadFromData(content)
        pixmap = QPixmap(img)
        if not pixmap.isNull():
            self.table_overview.set_cover(pixmap)

    def show_album(self, album):
        pass
