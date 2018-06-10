from PyQt5.QtWidgets import QLineEdit


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setPlaceholderText('歌曲、歌手、专辑、用户')
