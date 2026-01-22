"""
all metadata related widgets, for example: cover, and so on.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QSpacerItem,
    QFrame,
    QSizePolicy,
)

from feeluown.gui.helpers import elided_text
from feeluown.gui.components import FavButton
from feeluown.i18n import t
from .cover_label import CoverLabelV2

if TYPE_CHECKING:
    from feeluown.gui.app import GuiApp  # type: ignore


class getset_property:
    def __init__(self, name):
        self.name = name
        self.name_real = "_" + name

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
        self.model = None

    def on_property_updated(self, name):
        pass

    # TODO: use metaclass
    title = getset_property("title")
    subtitle = getset_property("subtitle")
    source = getset_property("source")
    cover = getset_property("cover")
    created_at: datetime = getset_property("created_at")
    updated_at: datetime = getset_property("updated_at")
    songs_count = getset_property("songs_count")
    creator = getset_property("creator")
    # YYYY-mm-dd
    released_at: str = getset_property("released_at")
    model = getset_property("model")


class TableMetaWidget(MetaWidget):
    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)

        self.cover_label = CoverLabelV2(self)
        # these widgets are in right layout
        self.title_label = QLabel(self)
        self.fav_button = FavButton(app=app, size=(13, 13), parent=self)
        self.meta_label = QLabel(self)
        # this spacer item is used as a stretch in right layout,
        # it's  width and height is not so important, we set them to 0
        self.text_spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        # self.title_label.setTextFormat(Qt.TextFormat.RichText)
        self.meta_label.setTextFormat(Qt.TextFormat.RichText)

        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        font = self.font()
        font.setPixelSize(20)
        font.setWeight(QFont.Weight.DemiBold)

        self.cover_label.setMinimumWidth(150)
        self.cover_label.setMaximumWidth(200)
        self.title_label.setFont(font)

        self._v_layout = QVBoxLayout(self)
        self._h_layout = QHBoxLayout()
        self._right_layout = QVBoxLayout()
        self._right_layout.addStretch(0)

        self._title_row_layout = QHBoxLayout()
        self._title_row_layout.addWidget(self.title_label)
        self._title_row_layout.addWidget(self.fav_button)
        self._title_row_layout.setSpacing(10)
        self._title_row_layout.addStretch(0)
        self._title_row_layout.setAlignment(
            self.fav_button, Qt.AlignmentFlag.AlignCenter
        )

        self._right_layout.addLayout(self._title_row_layout)
        self._right_layout.addWidget(self.meta_label)
        self._h_layout.addWidget(self.cover_label)
        self._h_layout.setAlignment(self.cover_label, Qt.AlignmentFlag.AlignTop)
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
        self._right_layout.setAlignment(tabbar, Qt.AlignmentFlag.AlignLeft)

    def set_cover_image(self, image):
        if image is not None:
            self.cover_label.show()
            self._right_layout.addItem(self.text_spacer)
        self.cover_label.show_img(image)
        self.updateGeometry()

    def on_property_updated(self, name):
        if name in (
            "created_at",
            "updated_at",
            "songs_count",
            "creator",
            "source",
            "released_at",
        ):
            self._refresh_meta_label()
        elif name in ("title", "subtitle"):
            self._refresh_title()
        elif name == "cover":
            self._refresh_cover()
        elif name == "model":
            self._refresh_fav_button()

    def _refresh_meta_label(self):
        creator = self.creator
        # icon: 👤
        creator_part = creator if creator else ""
        released_part = created_part = updated_part = songs_count_part = source_part = (
            ""
        )
        if self.source:
            source_part = f'<code style="color: gray;">{self.source}</code>'
        if self.updated_at:
            updated_part = t("meta-updated-at", unixTimestamp=self.updated_at)
        if self.created_at:
            created_part = t("meta-created-at", unixTimestamp=self.created_at)
        if self.released_at:
            try:
                year, month, day = map(int, self.released_at.split("-"))
            except Exception:
                year, month, day = 1970, 1, 1
            released_dt = date(year=year, month=month, day=day)
            released_part = t("meta-released-at", unixTimestamp=released_dt)

        if self.songs_count is not None:
            songs_count_part = t("meta-amount-songs", songsCount=self.songs_count)
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
            content = " • ".join(valid_parts)
            text = f"<span>{content}</span>"
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
            title = elided_text(
                self.title, self.parent().width(), self.title_label.font()
            )
            self.title_label.setText(title)
        else:
            self.title_label.hide()

    def _refresh_fav_button(self):
        self.fav_button.set_model(self.model)
        if self.model:
            self.fav_button.show()
        else:
            self.fav_button.hide()

    def _refresh(self):
        self._refresh_title()
        self._refresh_meta_label()
        self._refresh_cover()
        self._refresh_fav_button()

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
