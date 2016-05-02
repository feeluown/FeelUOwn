import requests

from PyQt5.QtGui import QImage, QPixmap, QColor


def pixmap_from_url(url, callback=None):
    res = requests.get(url)
    if res.status_code != 200:
        return None
    img = QImage()
    img.loadFromData(res.content)
    if callback is not None:
        callback(QPixmap(img))
    else:
        return QPixmap(img)


def parse_ms(ms):
    minute = int(ms / 60000)
    second = int((ms % 60000) / 1000)
    return minute, second


def lighter(color, degree=1, a=255):
    r, g, b = color.red(), color.green(), color.blue()
    r = r + 10 * degree if (r + 10 * degree) < 255 else 255
    g = g + 10 * degree if (g + 10 * degree) < 255 else 255
    b = b + 10 * degree if (b + 10 * degree) < 255 else 255
    return QColor(r, g, b, a)


def darker(color, degree=1, a=255):
    r, g, b = color.red(), color.green(), color.blue()
    r = r - 10 * degree if (r - 10 * degree) > 0 else 0
    g = g - 10 * degree if (g - 10 * degree) > 0 else 0
    b = b - 10 * degree if (b - 10 * degree) > 0 else 0
    return QColor(r, g, b, a)
