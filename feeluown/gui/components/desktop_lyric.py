from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath,
)
from PyQt6.QtWidgets import (
    QSizeGrip,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from feeluown.gui.components.nowplaying import NowplayingLyricView
from feeluown.gui.helpers import elided_text, to_cover_media_by_source
from feeluown.utils.aio import run_afn


class _FadingLyricDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        size = super().sizeHint(option, index)
        size.setHeight(round(QFontMetrics(option.font).height() * 1.4))
        return size

    def paint(self, painter, option, index):
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        view = self.parent()
        painter.save()
        if index == view.currentIndex():
            option.font.setWeight(QFont.Weight.DemiBold)
            painter.setPen(QColor("#ffffff"))
        else:
            gradient = QLinearGradient(0, 0, 0, view.viewport().height())
            gradient.setColorAt(0, QColor(235, 238, 245, 25))
            gradient.setColorAt(0.5, QColor(235, 238, 245, 180))
            gradient.setColorAt(1, QColor(235, 238, 245, 25))
            pen = painter.pen()
            pen.setBrush(gradient)
            painter.setPen(pen)
        painter.setFont(option.font)
        painter.drawText(
            option.rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextSingleLine,
            elided_text(option.text, option.rect.width(), option.font),
        )
        painter.restore()


class DesktopLyricCard(QWidget):
    """Multiline desktop lyrics over a softened album cover."""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._cover = QImage()
        self._setup_ui()
        app.player.metadata_changed.connect(self._on_metadata_changed, aioqueue=True)
        self._on_metadata_changed(app.player.current_metadata)

    def _setup_ui(self):
        self.drag_area = QWidget(self)
        self.drag_area.setFixedHeight(12)
        self.drag_area.setCursor(Qt.CursorShape.SizeAllCursor)

        self.lyric_view = NowplayingLyricView(self._app, parent=self)
        self.lyric_view.setItemDelegate(_FadingLyricDelegate(self.lyric_view))
        self.lyric_view.setAutoFillBackground(False)
        self.lyric_view.viewport().setAutoFillBackground(False)
        self.lyric_view.set_lyric(self._app.live_lyric.current_lyrics[0])
        self.size_grip = QSizeGrip(self)
        self.size_grip.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 14, 22, 12)
        layout.setSpacing(6)
        layout.addWidget(self.drag_area)
        layout.addWidget(self.lyric_view, 1)
        layout.addWidget(self.size_grip, 0, Qt.AlignmentFlag.AlignRight)

    def _on_metadata_changed(self, metadata):
        self._cover = QImage()
        self.update()
        artwork = metadata.get("artwork", "")
        if artwork:
            run_afn(
                self._load_cover, artwork, metadata.get("source", ""),
                metadata.get("uri", artwork) or artwork,
            )

    async def _load_cover(self, artwork, source, uid):
        media = to_cover_media_by_source(self._app.library, source, artwork)
        content = await self._app.img_mgr.get(media, uid)
        metadata = self._app.player.current_metadata
        # A cover request may finish after the player has moved to another song.
        if (artwork, source) != (
            metadata.get("artwork", ""), metadata.get("source", ""),
        ):
            return
        if content is None:
            return
        image = QImage.fromData(content)
        # Keep the background soft and avoid resampling a full-size cover on repaint.
        self._cover = image.scaled(
            96, 96, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, 18, 18)
        painter.setClipPath(path)
        painter.fillPath(path, QColor(23, 25, 33, 245))
        if not self._cover.isNull():
            size = self._cover.size()
            size.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
            target = QRectF(0, 0, size.width(), size.height())
            target.moveCenter(rect.center())
            painter.drawImage(target, self._cover)
            painter.fillPath(path, QColor(12, 14, 20, 175))
        painter.setPen(QColor(255, 255, 255, 28))
        painter.drawPath(path)
