import requests

from PyQt5.QtGui import QImage, QPixmap


def pixmap_from_url(url, callback=None):
    res = requests.get(url)
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
