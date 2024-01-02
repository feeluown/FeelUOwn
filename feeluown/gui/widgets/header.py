from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel


class BaseHeader(QLabel):
    def __init__(self, font_size, *args, **kwargs):
        super().__init__(*args, **kwargs)

        font = self.font()
        font.setPixelSize(font_size)
        self.setFont(font)


class LargeHeader(BaseHeader):
    def __init__(self, *args, **kwargs):
        super().__init__(20, *args, **kwargs)

        font = self.font()
        font.setWeight(QFont.DemiBold)
        self.setFont(font)


class MidHeader(BaseHeader):
    def __init__(self, *args, **kwargs):
        super().__init__(16, *args, **kwargs)
