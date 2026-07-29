"""
Desktop (standalone window) scrolling lyrics view.

It is the multi-line counterpart of the historical single-line lyric
window. It reuses :class:`feeluown.gui.widgets.lyric.LyricView` and is
app-dependent because it subscribes to ``app.live_lyric`` directly.
"""
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetrics, QPalette
from PyQt6.QtWidgets import QAbstractItemView

from feeluown.gui.widgets.lyric import LyricView
from feeluown.i18n import t

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


class DesktopLyricView(LyricView):
    """A LyricView tuned for the standalone lyric window.

    The view renders multiple lines around the current line. It connects
    to ``app.live_lyric`` signals to follow playback. When the underlying
    ``Lyric`` is ``None``, it shows a single "lyric-not-available" hint
    line so the window never looks broken.
    """

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        self._alignment = Qt.AlignmentFlag.AlignCenter
        self._highlight_font_size = 24
        self._item_spacing = 6
        self._empty_placeholder_text = t("lyric-not-available")

        font = self.font()
        font.setPixelSize(15)
        self.setFont(font)

        # The view must stay transparent so the parent (which draws the
        # rounded background) remains visible. We never let the user's
        # background color leak into the view's background.
        self.viewport().setAutoFillBackground(False)
        self.viewport().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        initial_palette = self.palette()
        self._apply_transparent_palette(initial_palette)
        super().setPalette(initial_palette)

        self._app.live_lyric.lyrics_changed.connect(
            self.on_lyric_changed, aioqueue=True
        )
        self._app.live_lyric.line_changed.connect(self.on_line_changed, weak=True)

        # Seed the view from the current lyric so the window is not blank
        # when it is constructed while a song is already playing.
        current_lyrics = self._app.live_lyric.current_lyrics
        current_lyric = current_lyrics[0] if current_lyrics else None
        self.on_lyric_changed(current_lyric)

    def _apply_transparent_palette(self, palette: QPalette) -> None:
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.AlternateBase, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.Highlight, Qt.GlobalColor.transparent)
        palette.setColor(
            QPalette.ColorRole.HighlightedText,
            palette.color(QPalette.ColorRole.Text),
        )

    def _create_item(self, line):
        item = super()._create_item(line)
        item.setBackground(QBrush(QColor(0, 0, 0, 0)))
        size_hint = self._item_size_hint(line, self.font())
        size_hint = QSize(size_hint.width(), size_hint.height() + self._item_spacing)
        item.setData(Qt.ItemDataRole.UserRole, size_hint)
        item.setSizeHint(size_hint)
        return item

    def on_item_changed(self, current, previous):
        super().on_item_changed(current, previous)
        if current is None:
            return
        render_font = QFont(self.font())
        render_font.setPixelSize(self._highlight_font_size)
        size_hint = self._item_size_hint(current.text(), render_font)
        current.setSizeHint(
            QSize(size_hint.width(), size_hint.height() + self._item_spacing)
        )

    def reset_item(self, item):
        super().reset_item(item)
        if item is None:
            return
        size_hint = item.data(Qt.ItemDataRole.UserRole)
        if size_hint is not None:
            item.setSizeHint(size_hint)
        item.setBackground(QBrush(QColor(0, 0, 0, 0)))

    def on_lyric_changed(self, lyric, *_, **__):
        if lyric is None:
            self.clear()
            item = self._create_item(self._empty_placeholder_text)
            self.addItem(item)
            self.setCurrentItem(item)
            return
        self.set_lyric(lyric)

    def setPalette(self, palette):  # type: ignore[override]
        new_palette = QPalette(palette)
        self._apply_transparent_palette(new_palette)
        super().setPalette(new_palette)

    def setFont(self, font):  # type: ignore[override]
        super().setFont(font)
        self._refresh_item_sizes()

    def _refresh_item_sizes(self):
        current_item = self.currentItem()
        view_font = self.font()
        for i in range(self.count()):
            item = self.item(i)
            if item is None:
                continue
            if item is current_item:
                render_font = QFont(view_font)
                render_font.setPixelSize(self._highlight_font_size)
            else:
                render_font = view_font
            size_hint = self._item_size_hint(item.text(), render_font)
            if item is current_item:
                size_hint = QSize(
                    size_hint.width(), size_hint.height() + self._item_spacing
                )
            item.setData(Qt.ItemDataRole.UserRole, size_hint)
            item.setSizeHint(size_hint)

    def scroll_to_current(self):
        if self._lyric is None:
            return
        index = self._lyric.current_index
        if index is None:
            return
        item = self.item(index)
        if item is None:
            return
        self.setCurrentItem(item)
        self.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)

    def _item_size_hint(self, line, font):
        rect = QFontMetrics(font).boundingRect(line)
        return QSize(rect.width(), rect.height())

    def item_slot_height(self):
        """Vertical slot one line occupies in the view."""
        line_height = self.fontMetrics().height()
        if line_height <= 0:
            return 0
        return line_height + self._item_spacing
