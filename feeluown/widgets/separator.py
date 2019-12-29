from PyQt5.QtWidgets import QFrame


stylesheet = '''
QFrame[frameShape="4"],
QFrame[frameShape="5"]
{{
    border: none;
    background: {};
}}
'''


class Separator(QFrame):
    def __init__(self, orientation='horizontal', parent=None):
        super().__init__(parent)

        self._app = parent

        if orientation == 'horizontal':
            self.setFrameShape(QFrame.HLine)
        else:
            self.setFrameShape(QFrame.VLine)

        if self._app.theme_mgr.theme == 'dark':
            self.setStyleSheet(stylesheet.format('#232323'))
            self.setMaximumHeight(1)
        else:
            self.setFrameShadow(QFrame.Sunken)
