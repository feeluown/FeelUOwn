from PyQt6.QtGui import QImage, QColor

from feeluown.gui.thumbnail_cache import (
    ScaledPixmapCache,
    ThumbnailImageCache,
    scale_image,
)


def test_thumbnail_image_cache_evicts_least_recently_used_item_by_count():
    cache = ThumbnailImageCache(max_items=2)
    cache.set("a", None)
    cache.set("b", None)

    cached, _ = cache.get("a")
    assert cached is True

    cache.set("c", None)

    assert cache.get("a")[0] is True
    assert cache.get("b")[0] is False
    assert cache.get("c")[0] is True


def test_thumbnail_image_cache_evicts_by_total_image_bytes():
    cache = ThumbnailImageCache(max_bytes=16, max_items=10)
    cache.set("a", QImage(2, 2, QImage.Format.Format_ARGB32))
    cache.set("b", QImage(2, 2, QImage.Format.Format_ARGB32))

    assert cache.get("a")[0] is False
    assert cache.get("b")[0] is True


def test_thumbnail_image_cache_keeps_none_as_cached_value():
    cache = ThumbnailImageCache(max_items=1)
    cache.set("missing", None)

    cached, image = cache.get("missing")

    assert cached is True
    assert image is None


def test_scale_image_keeps_small_images_unchanged():
    image = QImage(2, 3, QImage.Format.Format_ARGB32)

    scaled = scale_image(image, 4)

    assert scaled.cacheKey() == image.cacheKey()


def test_scale_image_limits_large_images_to_max_edge():
    image = QImage(20, 10, QImage.Format.Format_ARGB32)

    scaled = scale_image(image, 5)

    assert scaled.width() == 5
    assert scaled.height() == 2


def test_scaled_pixmap_cache_reuses_pixmap_for_same_image_and_fill_size(qapp):
    image = QImage(20, 10, QImage.Format.Format_ARGB32)
    image.fill(QColor("red"))
    cache = ScaledPixmapCache()

    pixmap = cache.scaled_to_fill(image, 8, 8, 1.0)
    cached_pixmap = cache.scaled_to_fill(image, 8, 8, 1.0)

    assert pixmap is not None
    assert cached_pixmap is not None
    assert pixmap.cacheKey() == cached_pixmap.cacheKey()


def test_scaled_pixmap_cache_returns_none_for_null_image(qapp):
    cache = ScaledPixmapCache()

    pixmap = cache.scaled_to_width(QImage(), 8, 1.0)

    assert pixmap is None
