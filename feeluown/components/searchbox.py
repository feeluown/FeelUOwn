from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QLineEdit


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setPlaceholderText('搜索歌曲、歌手、专辑、用户')
        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setTextMargins(5, 0, 0, 0)
