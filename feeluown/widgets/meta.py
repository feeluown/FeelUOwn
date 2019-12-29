from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem

from feeluown.widgets.desc_container import DescriptionContainer


class getset_property:
    def __init__(self, name):
        self.name = name
        self.name_real = '_' + name

    def __get__(self, instance, owner):
        if hasattr(instance, self.name_real):
            return getattr(instance, self.name_real)
        return None

    def __set__(self, instance, value):
        setattr(instance, self.name_real, value)
        instance.on_property_updated(self.name)


class MetaWidget(QWidget):

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

    def on_property_updated(self, name):
        pass

    # TODO: use metaclass
    title = getset_property('title')
    subtitle = getset_property('subtitle')
    desc = getset_property('desc')
    cover = getset_property('cover')
    created_at = getset_property('created_at')
    updated_at = getset_property('updated_at')
    songs_count = getset_property('songs_count')
    creator = getset_property('creator')
    is_artist = getset_property('is_artist')


class TableMetaWidget(MetaWidget):

    toggle_full_window_needed = pyqtSignal([bool])

    def __init__(self, toolbar, parent=None):
        super().__init__(parent=parent)

        self.title_label = QLabel(self)
        self.cover_label = QLabel(self)
        self.meta_label = QLabel(self)
        self.desc_container = DescriptionContainer(parent=self)
        self.toolbar = toolbar

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

    def on_property_updated(self, name):
        if name in ('created_at', 'updated_at', 'songs_count', 'creator'):
            self._refresh_meta_label()
        elif name in ('title', 'subtitle'):
            self._refresh_title()
        elif name == 'is_artist':
            self._refresh_toolbar()
        elif name == 'desc':
            self._refresh_desc()
        elif name == 'cover':
            self._refresh_cover()

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

    def _refresh_title(self):
        if self.title:
            self.title_label.show()
            self.title_label.setText('<h2>{}</h2>'.format(self.title))
        else:
            self.title_label.hide()

    def _refresh(self):
        self._refresh_title()
        self._refresh_meta_label()
        self._refresh_desc()
        self._refresh_cover()

    def set_cover_pixmap(self, pixmap):
        self.cover_label.show()
        self.cover_label.setPixmap(
            pixmap.scaledToWidth(self.cover_label.width(),
                                 mode=Qt.SmoothTransformation))

    def toggle_full_window(self):
        if self._is_fullwindow:
            self.toggle_full_window_needed.emit(False)
            self.setMaximumHeight(180)
        else:
            # generally, display height will be less than 4000px
            self.toggle_full_window_needed.emit(True)
            self.setMaximumHeight(4000)
        self._is_fullwindow = not self._is_fullwindow


class CollectionToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def songs_mode(self):
        pass

    def artists_mode(self):
        pass


class CollMetaWidget(MetaWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.toolbar = CollectionToolbar(self)

        self._title_label = QLabel(self)
        self._cover_label = QLabel(self)
        self._meta_label = QLabel(self)

        self._title_label.setTextFormat(Qt.RichText)
        self._meta_label.setTextFormat(Qt.RichText)
        self._top_mid_spacer = QSpacerItem(25, 0)

        self._layout = QVBoxLayout(self)
        self._top_layout = QHBoxLayout()
        self._top_right_layout = QVBoxLayout()
        self._bottom_layout = QHBoxLayout()

        self._setup_ui()

    def _setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._cover_label.setFixedWidth(150)
        self.setMaximumHeight(200)

        # top right layout
        self._top_right_layout.addStretch(0)
        self._top_right_layout.addWidget(self._title_label)
        self._top_right_layout.addSpacing(20)
        self._top_right_layout.addWidget(self._meta_label)
        self._top_right_layout.addStretch(0)

        self._top_layout.setContentsMargins(20, 20, 20, 20)
        self._top_layout.addWidget(self._cover_label)
        self._top_layout.addSpacerItem(self._top_mid_spacer)
        self._top_layout.addLayout(self._top_right_layout)

        self._layout.addLayout(self._top_layout)
        self._layout.addLayout(self._bottom_layout)

    def on_property_updated(self, name):
        if name in ('title', 'subtitle'):
            self._title_label.setText('<h2>{}</h2>'.format(self.title))
        elif name in ('created_at', 'updated_at', 'songs_count', 'creator'):
            parts = []
            if self.creator is not None:
                part = self.creator
                parts.append(part)
            if self.songs_count is not None:
                part = '{} 首歌曲'.format(self.songs_count)
                parts.append(part)
            if self.created_at is not None:
                created_at = datetime.fromtimestamp(self.created_at)
                part = '🕛 创建于 <code style="font-size: small">{}</code>'\
                    .format(created_at.strftime('%Y-%m-%d'))
                parts.append(part)
            if self.updated_at:
                updated_at = datetime.fromtimestamp(self.updated_at)
                part = '🕒 更新于 <code style="font-size: small">{}</code>'\
                    .format(updated_at.strftime('%Y-%m-%d'))
                parts.append(part)

            s = ' • '.join(parts)
            self._meta_label.setText(s)
        elif name == 'cover':
            if self.cover is None:
                self._cover_label.hide()
            else:
                self._cover_label.show()

    def set_cover_pixmap(self, pixmap):
        self._cover_label.show()
        self._cover_label.setPixmap(
            pixmap.scaledToWidth(self._cover_label.width(),
                                 mode=Qt.SmoothTransformation))

    # def resizeEvent(self, e):
    #     super().resizeEvent(e)
    #     width = e.size().width()
    #     self._cover_label.setMinimumWidth(width//3)
