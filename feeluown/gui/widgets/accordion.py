from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

from feeluown.gui.widgets.textbtn import TextButton


class ClickableHeader(QWidget):
    btn_text_fold = '△'
    btn_text_unfold = '▼'

    clicked = pyqtSignal()

    def __init__(self, header, checked=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.inner_header = header
        self.btn = TextButton(self._get_btn_text(checked))
        self.btn.setCheckable(True)
        self.btn.setChecked(checked)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.inner_header)
        self._layout.addStretch(0)
        self._layout.addWidget(self.btn)

        self.btn.clicked.connect(self.toggle)

    def toggle(self, checked):
        self.clicked.emit()
        self.btn.setText(self._get_btn_text(checked))

    def _get_btn_text(self, checked):
        return self.btn_text_unfold if checked else self.btn_text_fold


class Accordion(QWidget):
    """

    TODO: should be able to customize spacing.
    TODO: API will be changed.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def add_section(self,
                    header: QLabel,
                    content: QWidget,
                    header_spacing: int,
                    section_spacing: int):

        def toggle_content():
            if content.isVisible():
                content.hide()
            else:
                content.show()

        clickable_header = ClickableHeader(header, not content.isVisible())
        clickable_header.clicked.connect(toggle_content)

        self._layout.addWidget(clickable_header)
        self._layout.addSpacing(header_spacing)
        self._layout.addWidget(content)
        self._layout.addSpacing(section_spacing)
