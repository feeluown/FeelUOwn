"""
all metadata related widgets, for example: cover, and so on.
"""

from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtGui import QPainter, QBrush
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QFrame, QSizePolicy


class CoverLabel(QLabel):
    def __init__(self, parent=None, pixmap=None):
        super().__init__(parent=parent)

        self._pixmap = pixmap
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

    def show_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.updateGeometry()

    def paintEvent(self, e):
        """
        draw pixmap with border radius

        We found two way to draw pixmap with border radius,
        one is as follow, the other way is using bitmap mask,
        but in our practice, the mask way has poor render effects
        """
        if self._pixmap is None:
            return
        radius = 3
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        scaled_pixmap = self._pixmap.scaledToWidth(
            self.width(),
            mode=Qt.SmoothTransformation
        )
        size = scaled_pixmap.size()
        brush = QBrush(scaled_pixmap)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        y = (size.height() - self.height()) // 2
        painter.save()
        painter.translate(0, -y)
        rect = QRect(0, y, self.width(), self.height())
        painter.drawRoundedRect(rect, radius, radius)
        painter.restore()
        painter.end()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.updateGeometry()

    def sizeHint(self):
        super_size = super().sizeHint()
        if self._pixmap is None:
            return super_size
        h = (self.width() * self._pixmap.height()) // self._pixmap.width()
        # cover label height hint can be as large as possible, since the
        # parent width has been set maximumHeigh
        w = self.width()
        return QSize(w, min(w, h))


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


class MetaWidget(QFrame):

    def clear(self):
        self.title = None
        self.subtitle = None
        self.cover = None
        self.created_at = None
        self.updated_at = None
        self.creator = None
        self.songs_count = None

    def on_property_updated(self, name):
        pass

    # TODO: use metaclass
    title = getset_property('title')
    subtitle = getset_property('subtitle')
    cover = getset_property('cover')
    created_at = getset_property('created_at')
    updated_at = getset_property('updated_at')
    songs_count = getset_property('songs_count')
    creator = getset_property('creator')


class TableMetaWidget(MetaWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.cover_label = CoverLabel(self)
        # these three widgets are in right layout
        self.title_label = QLabel(self)
        self.meta_label = QLabel(self)
        # this spacer item is used as a stretch in right layout,
        # it's  width and height is not so important, we set them to 0
        self.text_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.title_label.setTextFormat(Qt.RichText)
        self.meta_label.setTextFormat(Qt.RichText)

        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        self.cover_label.setMaximumWidth(200)
        self._v_layout = QVBoxLayout(self)
        self._h_layout = QHBoxLayout()
        self._right_layout = QVBoxLayout()
        self._right_layout.addStretch(0)
        self._right_layout.addWidget(self.title_label)
        self._right_layout.addWidget(self.meta_label)
        self._h_layout.addWidget(self.cover_label)
        self._h_layout.setAlignment(self.cover_label, Qt.AlignTop)
        self._h_layout.addLayout(self._right_layout)
        self._h_layout.setStretchFactor(self._right_layout, 2)
        self._h_layout.setStretchFactor(self.cover_label, 1)
        self._h_layout.setContentsMargins(0, 30, 0, 0)
        self._h_layout.setSpacing(30)
        self._v_layout.addLayout(self._h_layout)

        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(5)

        # left margin is same as toolbar left margin
        self.layout().setContentsMargins(30, 0, 30, 0)
        self.layout().setSpacing(0)

    def add_tabbar(self, tabbar):
        self._right_layout.addWidget(tabbar)
        self._right_layout.setAlignment(self.parent().tabbar, Qt.AlignLeft)

    def set_cover_pixmap(self, pixmap):
        if pixmap is not None:
            self.cover_label.show()
            self._right_layout.addItem(self.text_spacer)
        self.cover_label.show_pixmap(pixmap)
        self.updateGeometry()

    def on_property_updated(self, name):
        if name in ('created_at', 'updated_at', 'songs_count', 'creator'):
            self._refresh_meta_label()
        elif name in ('title', 'subtitle'):
            self._refresh_title()
        elif name == 'cover':
            self._refresh_cover()

    def _refresh_meta_label(self):
        creator = self.creator
        # icon: 👤
        creator_part = creator if creator else ''
        created_part = updated_part = songs_count_part = ''
        if self.updated_at:
            updated_part = '🕒 更新于 <code style="font-size: small">{}</code>'\
                .format(self.updated_at.strftime('%Y-%m-%d'))
        if self.created_at:
            created_part = '🕛 创建于 <code style="font-size: small">{}</code>'\
                .format(self.created_at.strftime('%Y-%m-%d'))
        if self.songs_count is not None:
            text = self.songs_count if self.songs_count != -1 else '未知'
            songs_count_part = '<code style="font-size: small">{}</code> 首歌曲'\
                .format(text)
        if creator_part or updated_part or created_part or songs_count_part:
            parts = [creator_part, created_part, updated_part, songs_count_part]
            valid_parts = [p for p in parts if p]
            content = ' • '.join(valid_parts)
            text = '<span>{}</span>'.format(content)
            # TODO: add linkActivated callback for meta_label
            self.meta_label.setText(text)
            self.meta_label.show()
        else:
            self.meta_label.hide()

    def _refresh_cover(self):
        if not self.cover:
            self.cover_label.hide()
            self._right_layout.removeItem(self.text_spacer)
        else:
            self._right_layout.addItem(self.text_spacer)
        self.updateGeometry()

    def _refresh_title(self):
        if self.title:
            self.title_label.show()
            self.title_label.setText('<h2>{}</h2>'.format(self.title))
        else:
            self.title_label.hide()

    def _refresh(self):
        self._refresh_title()
        self._refresh_meta_label()
        self._refresh_cover()

    def sizeHint(self):
        super_size = super().sizeHint()
        if self.cover_label.isVisible():
            margins = self.layout().contentsMargins()
            v_margin = margins.top() + margins.bottom()
            height = self.cover_label.sizeHint().height() + v_margin
            return QSize(super_size.width(), height)
        return super_size

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # HELP: think about a more elegant way
        # Currently, right panel draw background image on meta widget
        # and bottom panel, when meta widget is resized, the background
        # image will also be scaled, so we need to repaint on bottom panel
        # and meta widget. However, by default, qt will only repaint
        # meta widget in this case, so we trigger bottom panel update manually
        self.parent()._app.ui.bottom_panel.update()


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
                part = '🕛 创建于 <code style="font-size: small">{}</code>'\
                    .format(self.created_at.strftime('%Y-%m-%d'))
                parts.append(part)
            if self.updated_at:
                part = '🕒 更新于 <code style="font-size: small">{}</code>'\
                    .format(self.updated_at.strftime('%Y-%m-%d'))
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
