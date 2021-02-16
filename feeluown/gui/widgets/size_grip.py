from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtWidgets import QSizeGrip
from PyQt5.QtGui import QTextOption, QPainter


class SizeGrip(QSizeGrip):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, e):
        painter = QPainter(self)
        option = QTextOption()
        option.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        painter.drawText(QRectF(self.rect()), '●', option)
