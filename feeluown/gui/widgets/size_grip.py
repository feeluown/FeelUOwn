from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtWidgets import QSizeGrip
from PyQt6.QtGui import QTextOption, QPainter


class SizeGrip(QSizeGrip):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, e):
        painter = QPainter(self)
        option = QTextOption()
        option.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        painter.drawText(QRectF(self.rect()), "●", option)
