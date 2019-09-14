from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFrame,
    QLabel,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
)

from feeluown.widgets.table_toolbar import SongsTableToolbar


class DescriptionContainer(QScrollArea):

    space_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel(self)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setWidget(self.label)
        self.setToolTip('按空格可以窗口全屏')

        self._setup_ui()

    def _setup_ui(self):
        self.label.setAlignment(Qt.AlignTop)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._layout = QVBoxLayout(self)
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
        elif key_code == Qt.Key_Space:
            self.space_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class TableMetaWidget(QWidget):

    toggle_full_window_needed = pyqtSignal([bool])

    class getset_property:
        def __init__(self, name, set_cb):
            self.name = name
            self.name_real = '_' + name
            self.set_cb = set_cb

        def __get__(self, instance, owner):
            if hasattr(instance, self.name_real):
                return getattr(instance, self.name_real)
            return None

        def __set__(self, instance, value):
            setattr(instance, self.name_real, value)
            if self.set_cb is not None:
                self.set_cb(instance)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.title_label = QLabel(self)
        self.cover_label = QLabel(self)
        self.meta_label = QLabel(self)
        self.desc_container = DescriptionContainer(parent=self)
        self.toolbar = SongsTableToolbar(parent=self)

        self.title_label.setTextFormat(Qt.RichText)
        self.meta_label.setTextFormat(Qt.RichText)

        self._is_fullwindow = False

        self._setup_ui()
        self._refresh()

        self.desc_container.space_pressed.connect(self.toggle_full_window)

    def _setup_ui(self):
        self.cover_label.setMinimumWidth(200)
        self.setMaximumHeight(180)
        self.title_label.setAlignment(Qt.AlignTop)
        self.meta_label.setAlignment(Qt.AlignTop)

        self._v_layout = QVBoxLayout(self)
        self._h_layout = QHBoxLayout()
        self._right_layout = QVBoxLayout()
        self._right_layout.addWidget(self.title_label)
        self._right_layout.addWidget(self.meta_label)
        self._right_layout.addWidget(self.desc_container)
        self._right_layout.addWidget(self.toolbar)
        self._right_layout.setAlignment(self.toolbar, Qt.AlignBottom)
        self._h_layout.addWidget(self.cover_label)
        self._h_layout.setAlignment(self.cover_label, Qt.AlignTop)
        self._h_layout.addLayout(self._right_layout)
        self._v_layout.addLayout(self._h_layout)

        self._h_layout.setContentsMargins(10, 10, 10, 10)
        self._h_layout.setSpacing(20)

        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(5)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def _refresh(self):
        self._refresh_title()
        self._refresh_meta_label()
        self._refresh_desc()
        self._refresh_cover()

    def _refresh_title(self):
        if self.title:
            self.title_label.show()
            self.title_label.setText('<h2>{}</h2>'.format(self.title))
        else:
            self.title_label.hide()

    def _refresh_meta_label(self):
        creator = self.creator
        creator_part = '👤 <a href="fuo://local/users/{}">{}</a>'\
            .format(creator, creator) if creator else ''
        created_part = updated_part = songs_count_part = ''
        if self.updated_at:
            updated_at = datetime.fromtimestamp(self.updated_at)
            updated_part = '🕒 更新于 <code style="font-size: small">{}</code>'\
                .format(updated_at.strftime('%Y-%m-%d'))
        if self.created_at:
            created_at = datetime.fromtimestamp(self.created_at)
            created_part = '🕛 创建于 <code style="font-size: small">{}</code>'\
                .format(created_at.strftime('%Y-%m-%d'))
        if self.songs_count is not None:
            text = self.songs_count if self.songs_count != -1 else '未知'
            songs_count_part = '歌曲数 <code style="font-size: small">{}</code>'\
                .format(text)
        if creator_part or updated_part or created_part or songs_count_part:
            parts = [creator_part, created_part, updated_part, songs_count_part]
            valid_parts = [p for p in parts if p]
            content = ' | '.join(valid_parts)
            text = '<span style="color: grey">{}</span>'.format(content)
            # TODO: add linkActivated callback for meta_label
            self.meta_label.setText(text)
            self.meta_label.show()
        else:
            self.meta_label.hide()

    def _refresh_desc(self):
        if self.desc:
            self.desc_container.show()
            self.desc_container.label.setText(self.desc)
        else:
            self.desc_container.hide()

    def _refresh_cover(self):
        if not self.cover:
            self.cover_label.hide()

    def _refresh_toolbar(self):
        if self.is_artist:
            self.toolbar.artist_mode()
        else:
            self.toolbar.songs_mode()

    def clear(self):
        self.title = None
        self.subtitle = None
        self.desc = None
        self.cover = None
        self.created_at = None
        self.updated_at = None
        self.creator = None
        self.is_artist = False
        self.songs_count = None

    def set_cover_pixmap(self, pixmap):
        self.cover_label.show()
        self.cover_label.setPixmap(
            pixmap.scaledToWidth(self.cover_label.width(),
                                 mode=Qt.SmoothTransformation))

    title = getset_property('title', _refresh_title)
    subtitle = getset_property('subtitle', _refresh_title)
    desc = getset_property('desc', _refresh_desc)
    cover = getset_property('cover', _refresh_cover)
    created_at = getset_property('created_at', _refresh_meta_label)
    updated_at = getset_property('updated_at', _refresh_meta_label)
    songs_count = getset_property('songs_count', _refresh_meta_label)
    creator = getset_property('creator', _refresh_meta_label)
    is_artist = getset_property('is_artist', _refresh_toolbar)

    def toggle_full_window(self):
        if self._is_fullwindow:
            self.toggle_full_window_needed.emit(False)
            self.setMaximumHeight(180)
        else:
            # generally, display height will be less than 4000px
            self.toggle_full_window_needed.emit(True)
            self.setMaximumHeight(4000)
        self._is_fullwindow = not self._is_fullwindow
