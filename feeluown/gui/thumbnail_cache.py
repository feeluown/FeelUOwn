from collections import OrderedDict
from typing import Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage


def scale_image(img: QImage, max_edge: int) -> QImage:
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
    def __init__(self, max_bytes: int = 64 * 1024 * 1024, max_items: int = 1024):
        self._max_bytes = max_bytes
        self._max_items = max_items
        self._total_bytes = 0
        self._items: "OrderedDict[str, Tuple[Optional[QImage], int]]" = OrderedDict()

    def __len__(self) -> int:
        return len(self._items)

    def get(self, key: str) -> Tuple[bool, Optional[QImage]]:
        if key not in self._items:
            return False, None
        img, size = self._items.pop(key)
        self._items[key] = (img, size)
        return True, img

    def set(self, key: str, img: Optional[QImage]) -> None:
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
