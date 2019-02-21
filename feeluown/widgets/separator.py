from PyQt5.QtWidgets import QFrame


class Separator(QFrame):
    def __init__(self, orientation='horizontal', parent=None):
        super().__init__(parent)

        if orientation == 'horizontal':
            self.setFrameShape(QFrame.HLine)
        else:
            self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
