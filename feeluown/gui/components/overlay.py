from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast

from PyQt6.QtCore import QEvent, QMargins, Qt
from PyQt6.QtGui import QColor, QPainter, QResizeEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout

from feeluown.gui.helpers import esc_hide_widget

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp


@dataclass
class AppOverlayOptions:
    adhoc: bool = False
    margins: Optional[QMargins] = None
    dim_background: bool = True
    close_on_focus_in: bool = True


class AppOverlayContainer(QWidget):
    """Base overlay widget that can be shown on top of other widgets.

    Features:
    - Semi-transparent background
    - Auto-resizing to parent
    - Click outside to close

    :param adhoc: If True, the overlay is destroyed when hidden.
    """

    def __init__(
        self,
        app: "GuiApp",
        body: QWidget,
        parent: Optional[QWidget] = None,
        options: Optional[AppOverlayOptions] = None,
    ):
        super().__init__(parent=parent)
        options = options or AppOverlayOptions()
        self._app = app
        self._adhoc = options.adhoc
        self._dim_background = options.dim_background
        self._close_on_focus_in = options.close_on_focus_in

        self.body = body
        self._layout = QHBoxLayout(self)
        margins = options.margins
        if margins is None:
            margins = QMargins(100, 80, 100, 80)
        self._layout.setContentsMargins(margins)
        self._layout.addWidget(self.body)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        # Add ClickFocus for the body so that when Overlay will not
        # get focus when user click the body.
        self.body.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._app.installEventFilter(self)

        esc_hide_widget(self)

    def showEvent(self, event):
        """Resize to parent when shown"""
        self.resize(self._app.size())
        super().showEvent(event)
        self.raise_()

    def hideEvent(self, event):
        """Uninstall event filter when hidden"""
        super().hideEvent(event)
        if self._adhoc is True:
            self.deleteLater()

    def paintEvent(self, event):
        """Draw semi-transparent background"""
        if self._dim_background is False:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

    def eventFilter(self, obj, event):
        """Handle parent resize events"""
        if self.isVisible() and obj == self._app and event.type() == QEvent.Type.Resize:
            event = cast(QResizeEvent, event)
            self.resize(event.size())
        return super().eventFilter(obj, event)

    def focusInEvent(self, event):
        if self._close_on_focus_in:
            self.hide()
        super().focusInEvent(event)
