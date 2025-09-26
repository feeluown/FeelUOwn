from PyQt6.QtWidgets import QFrame


stylesheet = """
QFrame[frameShape="4"],
QFrame[frameShape="5"]
{{
    border: none;
    background: {};
}}
"""


class Separator(QFrame):
    def __init__(self, app, orientation="horizontal"):
        super().__init__(parent=None)

        self._app = app

        if orientation == "horizontal":
            self.setFrameShape(QFrame.Shape.HLine)
        else:
            self.setFrameShape(QFrame.Shape.VLine)

        if self._app.theme_mgr.theme == "dark":
            self.setStyleSheet(stylesheet.format("#232323"))
            self.setMaximumHeight(1)
        else:
            self.setFrameShadow(QFrame.Shadow.Sunken)
