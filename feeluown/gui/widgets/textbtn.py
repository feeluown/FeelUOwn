from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton


class TextButton(QPushButton):
    def __init__(self, *args, height=None, **kwargs):
        """
        .. versionadded:: 3.9
            The *height* argument.
        """
        super().__init__(*args, **kwargs)

        self.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect, True)
        if height:
            self.setFixedHeight(height)
