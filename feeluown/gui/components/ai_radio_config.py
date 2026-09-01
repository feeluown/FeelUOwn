from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QPalette
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from feeluown.gui.helpers import secondary_text_color
from feeluown.i18n import t


class _AIRadioConfigFooter(QLabel):
    """Subtle clickable footer to view the active AI radio configuration."""

    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class AIRadioConfigView(QWidget):
    """Collapsible AI radio config: a subtle footer that expands to show the
    current preferences, avoidances and feedback notes in an inline label."""

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app
        self._expanded = False

        self._footer = _AIRadioConfigFooter(self)
        self._footer.setText(f"{t('ai-radio-config')} ›")
        self._footer.setCursor(Qt.CursorShape.PointingHandCursor)
        footer_font = self._footer.font()
        footer_font.setPixelSize(12)
        self._footer.setFont(footer_font)
        self._footer.setStyleSheet(
            "border-top: 1px solid rgba(128, 128, 128, 80); padding-top: 6px;"
        )
        self._footer.clicked.connect(self.toggle)

        self._details_label = QLabel("", self)
        self._details_label.setWordWrap(True)
        self._details_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        details_font = self._details_label.font()
        details_font.setPixelSize(12)
        self._details_label.setFont(details_font)
        self._details_label.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._footer)
        layout.addWidget(self._details_label)
        layout.addSpacing(6)

        self.setVisible(False)
        self.apply_palette()

    def set_visible(self, visible):
        super().setVisible(visible)
        if not visible:
            self.set_expanded(False)

    def toggle(self):
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded):
        if expanded and self._app.ai.get_active_radio() is None:
            return
        self._expanded = bool(expanded)
        self._details_label.setText(self._config_text() if self._expanded else "")
        self._details_label.setVisible(self._expanded)
        self.updateGeometry()

    def is_expanded(self):
        return self._expanded

    def apply_palette(self):
        color = secondary_text_color(QGuiApplication.palette())
        for label in (self._footer, self._details_label):
            pal = label.palette()
            pal.setColor(QPalette.ColorRole.WindowText, color)
            pal.setColor(QPalette.ColorRole.Text, color)
            label.setPalette(pal)
        self.update()

    def _config_text(self):
        radio = self._app.ai.get_active_radio()
        if radio is None:
            return ""
        lines = []
        for title, items in (
            (t("ai-radio-config-preferences"), radio.preferences),
            (t("ai-radio-config-avoidances"), radio.avoidances),
            (t("ai-radio-config-notes"), radio.preference_notes),
        ):
            lines.append(title)
            if items:
                lines.extend(f"- {item}" for item in items)
            else:
                lines.append(f"- {t('ai-radio-config-empty')}")
        return "\n".join(lines)
