from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QPixmapCache


class ThumbnailCache:
    def __init__(self, cache_limit_kb: int = 128 * 1024) -> None:
        if QPixmapCache.cacheLimit() < cache_limit_kb:
            QPixmapCache.setCacheLimit(cache_limit_kb)

    def scale_image(self, img: QImage, max_edge: int) -> QImage:
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
