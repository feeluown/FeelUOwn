from collections import OrderedDict
from typing import Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QPixmapCache


class ThumbnailCache:
    def __init__(self, cache_limit_kb: int = 128 * 1024) -> None:
        if QPixmapCache.cacheLimit() < cache_limit_kb:
            QPixmapCache.setCacheLimit(cache_limit_kb)

    def pixmap_for_width(
        self,
        img: QImage,
        width: int,
        device_pixel_ratio: float,
        key_prefix: str,
    ) -> QPixmap | None:
        if img.isNull() or width <= 0:
            return None
        cache_key = f"{key_prefix}:{img.cacheKey()}:{width}@{device_pixel_ratio}"
        pixmap = QPixmapCache.find(cache_key)
        if pixmap is not None and not pixmap.isNull():
            return pixmap

        scaled = img.scaledToWidth(
            int(width * device_pixel_ratio),
            Qt.TransformationMode.SmoothTransformation,
        )
        pixmap = QPixmap.fromImage(scaled)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        QPixmapCache.insert(cache_key, pixmap)
        return pixmap

    def pixmap_for_image(
        self,
        img: QImage,
        width: int,
        height: int,
        device_pixel_ratio: float,
        key_prefix: str,
    ) -> QPixmap | None:
        if img.isNull() or width <= 0 or height <= 0:
            return None
        cache_key = (
            f"{key_prefix}:{img.cacheKey()}:{width}x{height}@{device_pixel_ratio}"
        )
        pixmap = QPixmapCache.find(cache_key)
        if pixmap is not None and not pixmap.isNull():
            return pixmap

        if img.width() / img.height() > width / height:
            scaled = img.scaledToHeight(
                int(height * device_pixel_ratio),
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            scaled = img.scaledToWidth(
                int(width * device_pixel_ratio),
                Qt.TransformationMode.SmoothTransformation,
            )

        pixmap = QPixmap.fromImage(scaled)
        pixmap.setDevicePixelRatio(device_pixel_ratio)
        QPixmapCache.insert(cache_key, pixmap)
        return pixmap


def scale_image(img: QImage, max_edge: int) -> QImage:
    """Return an image capped by max_edge while preserving its aspect ratio."""
    if img.isNull():
        return img
    if img.width() <= max_edge and img.height() <= max_edge:
        return img
    return img.scaled(
        max_edge,
        max_edge,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class ThumbnailImageCache:
    """LRU cache for decoded thumbnail images.

    The cache stores QImage objects instead of QPixmap objects so model-side
    memory is bounded without depending on paint-device resources.
    """

    def __init__(self, max_bytes: int = 64 * 1024 * 1024, max_items: int = 1024):
        self._max_bytes = max_bytes
        self._max_items = max_items
        self._total_bytes = 0
        self._items: "OrderedDict[str, Tuple[Optional[QImage], int]]" = OrderedDict()

    def __len__(self) -> int:
        return len(self._items)

    def get(self, key: str) -> Tuple[bool, Optional[QImage]]:
        """Return (cached, image); image may be None for a cached miss."""
        if key not in self._items:
            return False, None
        img, size = self._items.pop(key)
        self._items[key] = (img, size)
        return True, img

    def set(self, key: str, img: Optional[QImage]) -> None:
        """Store an image result, including None for models without artwork."""
        size = self._image_cost(img)
        if key in self._items:
            _, old_size = self._items.pop(key)
            self._total_bytes -= old_size
        self._items[key] = (img, size)
        self._total_bytes += size
        self._evict_if_needed()

    def remove(self, key: str) -> None:
        if key not in self._items:
            return
        _, size = self._items.pop(key)
        self._total_bytes -= size

    def clear(self) -> None:
        self._items.clear()
        self._total_bytes = 0

    def _evict_if_needed(self) -> None:
        while self._items and (
            self._total_bytes > self._max_bytes or len(self._items) > self._max_items
        ):
            _, (_, size) = self._items.popitem(last=False)
            self._total_bytes -= size

    def _image_cost(self, img: Optional[QImage]) -> int:
        if img is None or img.isNull():
            return 0
        try:
            return img.sizeInBytes()
        except AttributeError:
            return img.bytesPerLine() * img.height()
