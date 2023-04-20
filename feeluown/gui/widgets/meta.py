"""
all metadata related widgets, for example: cover, and so on.
"""

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, \
    QSpacerItem, QFrame, QSizePolicy

from feeluown.gui.helpers import elided_text
from .cover_label import CoverLabelV2


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
        self.source = None
        self.cover = None
        self.created_at = None
        self.updated_at = None
        self.creator = None
        self.songs_count = None
        self.released_at = None

    def on_property_updated(self, name):
        pass

    # TODO: use metaclass
    title = getset_property('title')
    subtitle = getset_property('subtitle')
    source = getset_property('source')
    cover = getset_property('cover')
    created_at = getset_property('created_at')  # datetime
    updated_at = getset_property('updated_at')  # datetime
    songs_count = getset_property('songs_count')
    creator = getset_property('creator')
    released_at = getset_property('released_at')  # str


class TableMetaWidget(MetaWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.cover_label = CoverLabelV2(self)
        # these three widgets are in right layout
        self.title_label = QLabel(self)
        self.meta_label = QLabel(self)
        # this spacer item is used as a stretch in right layout,
        # it's  width and height is not so important, we set them to 0
        self.text_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # self.title_label.setTextFormat(Qt.RichText)
        self.meta_label.setTextFormat(Qt.RichText)

        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        font = self.font()
        font.setPixelSize(20)
        font.setWeight(QFont.DemiBold)

        self.cover_label.setMinimumWidth(150)
        self.cover_label.setMaximumWidth(200)
        self.title_label.setFont(font)

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
        self.layout().setContentsMargins(0, 0, 30, 0)
        self.layout().setSpacing(0)

    def add_tabbar(self, tabbar):
        self._right_layout.addWidget(tabbar)
        self._right_layout.setAlignment(tabbar, Qt.AlignLeft)

    def set_cover_image(self, image):
        if image is not None:
            self.cover_label.show()
            self._right_layout.addItem(self.text_spacer)
        self.cover_label.show_img(image)
        self.updateGeometry()

    def on_property_updated(self, name):
        if name in ('created_at', 'updated_at', 'songs_count', 'creator',
                    'source', 'released_at'):
            self._refresh_meta_label()
        elif name in ('title', 'subtitle'):
            self._refresh_title()
        elif name == 'cover':
            self._refresh_cover()

    def _refresh_meta_label(self):
        creator = self.creator
        # icon: 👤
        creator_part = creator if creator else ''
        released_part = created_part = updated_part = songs_count_part = source_part = ''
        if self.source:
            source_part = f'<code style="color: gray;">{self.source}</code>'
        if self.updated_at:
            updated_part = '🕒 更新于 <code style="font-size: small">{}</code>'\
                .format(self.updated_at.strftime('%Y-%m-%d'))
        if self.created_at:
            created_part = '🕛 创建于 <code style="font-size: small">{}</code>'\
                .format(self.created_at.strftime('%Y-%m-%d'))
        if self.released_at:
            released_part = f'🕛 发布于 <code style="font-size: small">{self.released_at}</code>'  # noqa
        if self.songs_count is not None:
            text = self.songs_count if self.songs_count != -1 else '未知'
            songs_count_part = f'<code style="font-size: small">{text}</code> 首歌曲'
        parts = [
            creator_part,
            created_part,
            updated_part,
            songs_count_part,
            released_part,
            source_part,
        ]
        valid_parts = [p for p in parts if p]
        if valid_parts:
            content = ' • '.join(valid_parts)
            text = f'<span>{content}</span>'
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
            self.title_label.setToolTip(self.title)
            # Please refresh when the widget is resized.
            title = elided_text(self.title,
                                self.title_label.width(),
                                self.title_label.font())
            self.title_label.setText(title)
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
        self._refresh_title()
        # HELP: think about a more elegant way
        # Currently, right panel draw background image on meta widget
        # and bottom panel, when meta widget is resized, the background
        # image will also be scaled, so we need to repaint on bottom panel
        # and meta widget. However, by default, qt will only repaint
        # meta widget in this case, so we trigger bottom panel update manually
        #
        # type ignore: parent should be TableContainer.
        self.parent()._app.ui.bottom_panel.update()  # type: ignore[attr-defined]
