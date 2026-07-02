"""
A Dynamic-Island-style status bar showing current song info.

In compact state (playing, no hover): shows cover + current lyric line.
In expanded state (paused or hover): shows cover + song title/artist + controls.
Hidden when no song is playing.
"""

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING

from PyQt6.QtCore import QRectF, Qt, QTimer
from PyQt6.QtGui import QGuiApplication, QPainter, QPalette
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QWidget,
)

from feeluown.gui.helpers import elided_text
from feeluown.gui.widgets.cover_label import CoverLabelV2
from feeluown.gui.widgets.selfpaint_btn import (
    PlayPauseButton,
    PlayNextButton,
    PlayPreviousButton,
)
from feeluown.gui.components.line_song import LineSongLabel
from feeluown.player import State
from feeluown.player.lyric import Line
from feeluown.utils.aio import run_afn

if TYPE_CHECKING:
    from feeluown.app.gui_app import GuiApp

logger = logging.getLogger(__name__)

# Sizing constants
ISLAND_HEIGHT = 36
COVER_COMPACT = 20
COVER_EXPANDED = 24
BTN_SIZE = 22
ANIMATION_STEP = 12  # px per tick at 16ms (~750 px/s)
COMPACT_MIN_WIDTH = 96
EXPANDED_WIDTH = 320
COMPACT_MAX_WIDTH = EXPANDED_WIDTH
CONTENT_SWITCH_RATIO = 0.6  # switch content visibility at 60% progress
CONTENT_SPACING = 8
PADDING_LEFT = 7
PADDING_RIGHT = 8
CONTROL_SPACING = 2


class DynamicIslandStatusBar(QWidget):
    """A pill-shaped player status bar for the AI chat input.

    Uses system palette colors and reuses existing components.
    """

    def __init__(self, app: "GuiApp", parent=None):
        super().__init__(parent=parent)
        self._app = app

        # Hover and animation state
        self._hovered = False
        self._animating = False
        self._expansion_state = "compact"  # "compact" | "expanded"
        self._anim_from = 0  # width at animation start
        self._anim_to = 0  # target width
        self._anim_current = 0  # current animated width
        self._has_song = False
        self._compact_text = ""

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick_animation)

        self._setup_ui()
        self._connect_signals()
        self.hide()
        self._sync_current_state()

    def _setup_ui(self):
        """Initialize child widgets and layout."""
        self.setFixedHeight(ISLAND_HEIGHT)
        self.setMinimumWidth(COMPACT_MIN_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Cover art
        self._cover = CoverLabelV2(self._app, radius=3, parent=self)
        self._cover.setFixedSize(COVER_COMPACT, COVER_COMPACT)

        # Lyric label (visible in compact state)
        self._lyric_label = QLabel("", self)
        self._lyric_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lyric_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )

        # Song title label (visible in expanded state)
        # Reuses LineSongLabel which handles "title • artists" format,
        # elision, and hover marquee scrolling.
        self._song_label = LineSongLabel(self._app, parent=self)
        self._song_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._song_label.hide()

        # Control buttons (visible in expanded state)
        self._prev_btn = PlayPreviousButton(length=BTN_SIZE)
        self._pp_btn = PlayPauseButton(length=BTN_SIZE, draw_circle=False)
        self._pp_btn.setCheckable(True)
        self._next_btn = PlayNextButton(length=BTN_SIZE)
        for btn in (self._prev_btn, self._pp_btn, self._next_btn):
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self._control_widget = QWidget(self)
        control_layout = QHBoxLayout(self._control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(CONTROL_SPACING)
        control_layout.addWidget(self._prev_btn)
        control_layout.addWidget(self._pp_btn)
        control_layout.addWidget(self._next_btn)
        self._control_widget.hide()

        # Main layout: cover | lyric/song_label (stretch) | controls
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(PADDING_LEFT, 0, PADDING_RIGHT, 0)
        self._layout.setSpacing(CONTENT_SPACING)
        self._layout.addWidget(self._cover)
        self._layout.addWidget(
            self._lyric_label,
            1,
            Qt.AlignmentFlag.AlignCenter,
        )
        self._layout.addWidget(self._song_label, 1)
        self._layout.addWidget(self._control_widget)
        self.setFixedWidth(self._calc_compact_width())

    def _connect_signals(self):
        """Wire up player and lyric signals."""
        self._app.player.metadata_changed.connect(
            self._on_metadata_changed, aioqueue=True
        )
        self._app.player.state_changed.connect(
            self._on_player_state_changed, aioqueue=True
        )
        self._app.live_lyric.line_changed.connect(
            self._on_lyric_line_changed
        )

        # Control button actions
        self._prev_btn.clicked.connect(self._app.playlist.previous)
        self._pp_btn.clicked.connect(self._app.player.toggle)
        self._next_btn.clicked.connect(self._app.playlist.next)
        self._app.player.state_changed.connect(
            self._on_player_state_for_pp_btn, aioqueue=True
        )

    # ---- public methods ----

    # ---- protected slots ----

    def _on_player_state_for_pp_btn(self, state):
        """Sync play/pause button checked state with player."""
        self._pp_btn.setChecked(state == State.playing)

    def _on_metadata_changed(self, metadata):
        """Load cover art and prepare text when song changes.

        Visibility is controlled by _on_player_state_changed.
        LineSongLabel handles its own text updates via its internal
        metadata_changed connection.
        """
        if not isinstance(metadata, Mapping) or not metadata.get("title"):
            self._has_song = False
            self._set_compact_text("")
            self._cover.show_img(None)
            self.hide()
            return
        self._has_song = True

        artwork = metadata.get("artwork", "")
        source = metadata.get("source", "")
        artwork_uid = metadata.get("uri", artwork) or artwork
        if artwork:
            run_afn(
                self._cover.show_cover_with_source, artwork, source, artwork_uid
            )
        else:
            self._cover.show_img(None)

        state = self._app.player.state
        if state != State.stopped:
            self.show()
        if state == State.paused:
            self._start_expand()
        elif state == State.playing and not self._hovered:
            self._start_compact()

    def _on_player_state_changed(self, state):
        """Control visibility and expansion based on player state."""
        if state == State.stopped:
            self.hide()
        elif state == State.paused:
            if self._has_song:
                self.show()
            self._start_expand()
        elif state == State.playing:
            if self._has_song:
                self.show()
            if not self._hovered:
                self._start_compact()

    def _on_lyric_line_changed(self, line: Line):
        """Update lyric text in compact state."""
        if self._expansion_state != "compact":
            return

        self._set_compact_text(self._format_lyric_line(line))

    # ---- event handlers ----

    def enterEvent(self, event):
        self._hovered = True
        if self._app.player.state == State.playing:
            self._start_expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if self._app.player.state == State.playing:
            self._start_compact()
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Draw pill-shaped background using system palette colors.

        Uses QPalette.Base with adjusted alpha so the pill adapts
        automatically to light and dark themes without hardcoded colors.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pal = QGuiApplication.palette()
        bg = pal.color(QPalette.ColorRole.Base)
        bg.setAlpha(180 if self._hovered else 140)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        radius = self.height() / 2.0
        painter.drawRoundedRect(QRectF(self.rect()), radius, radius)

        super().paintEvent(event)

    # ---- private methods ----

    def _calc_compact_width(self):
        """Calculate the natural width when in compact state."""
        text = self._compact_text
        fm = self._lyric_label.fontMetrics()
        text_w = min(fm.horizontalAdvance(text), self._compact_text_max_width())
        if not text:
            text_w = 0
        # left pad + cover + gap + text + right pad
        return max(
            COMPACT_MIN_WIDTH,
            min(
                (
                    PADDING_LEFT + COVER_COMPACT + CONTENT_SPACING +
                    text_w + PADDING_RIGHT
                ),
                COMPACT_MAX_WIDTH,
            ),
        )

    def _compact_text_max_width(self):
        return max(
            60,
            (
                EXPANDED_WIDTH - PADDING_LEFT - PADDING_RIGHT -
                COVER_COMPACT - CONTENT_SPACING
            ),
        )

    def _sync_current_state(self):
        self._on_metadata_changed(getattr(self._app.player, "current_metadata", None))
        self._on_player_state_for_pp_btn(self._app.player.state)
        if self._expansion_state == "compact":
            self._set_compact_text(
                self._format_lyric_line(self._app.live_lyric.current_line)
            )
        self._on_player_state_changed(self._app.player.state)

    def _format_lyric_line(self, line: Line):
        origin = getattr(line, "origin", "")
        if isinstance(origin, str) and origin:
            text = origin
            trans = getattr(line, "trans", "")
            if getattr(line, "has_trans", False) and isinstance(trans, str) and trans:
                text = f"{text} / {trans}"
            return text
        return ""

    def _set_compact_text(self, text):
        self._compact_text = text
        label_width = min(
            self._compact_text_max_width(),
            max(self._lyric_label.fontMetrics().horizontalAdvance(text), 1),
        )
        self._lyric_label.setFixedWidth(label_width)
        self._lyric_label.setText(
            elided_text(text, label_width, self._lyric_label.font())
        )
        self._lyric_label.setToolTip(text if text else "")

        # Adjust width to fit new lyric text
        if not self._animating:
            self.setFixedWidth(self._calc_compact_width())

    def _start_expand(self):
        """Begin expanding toward the expanded state."""
        if self._expansion_state == "expanded" and not self._animating:
            return
        if self._animating and self._anim_to > self._anim_from:
            return  # already expanding

        self._anim_from = self.width()
        self._anim_to = EXPANDED_WIDTH
        self._anim_current = self._anim_from
        self._animating = True
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)

    def _start_compact(self):
        """Begin collapsing toward the compact state."""
        if self._expansion_state == "compact" and not self._animating:
            return
        if self._animating and self._anim_to < self._anim_from:
            return  # already collapsing

        self._anim_from = self.width()
        self._anim_to = self._calc_compact_width()
        self._anim_current = self._anim_from
        self._animating = True
        if not self._anim_timer.isActive():
            self._anim_timer.start(16)

    def _tick_animation(self):
        """Advance the width animation by one step."""
        direction = 1 if self._anim_to > self._anim_from else -1
        self._anim_current += ANIMATION_STEP * direction

        # Clamp to target
        done = False
        if direction > 0 and self._anim_current >= self._anim_to:
            self._anim_current = self._anim_to
            done = True
        elif direction < 0 and self._anim_current <= self._anim_to:
            self._anim_current = self._anim_to
            done = True

        self.setFixedWidth(int(self._anim_current))

        # Switch content visibility at progress threshold
        total = abs(self._anim_to - self._anim_from)
        if total > 0:
            progress = abs(self._anim_current - self._anim_from) / total
            if progress >= CONTENT_SWITCH_RATIO:
                if direction > 0:
                    self._switch_to_expanded()
                else:
                    self._switch_to_compact()

        if done:
            self._anim_timer.stop()
            self._animating = False
            self._finalize_state()

    def _switch_to_expanded(self):
        """Show expanded content (song info + controls)."""
        if self._expansion_state == "expanded":
            return
        self._lyric_label.hide()
        self._song_label.show()
        self._control_widget.show()
        self._cover.setFixedSize(COVER_EXPANDED, COVER_EXPANDED)
        self._expansion_state = "expanded"

    def _switch_to_compact(self):
        """Show compact content (cover + lyric)."""
        if self._expansion_state == "compact":
            return
        self._lyric_label.show()
        self._song_label.hide()
        self._control_widget.hide()
        self._cover.setFixedSize(COVER_COMPACT, COVER_COMPACT)
        self._expansion_state = "compact"
        self._set_compact_text(
            self._format_lyric_line(self._app.live_lyric.current_line)
        )

    def _finalize_state(self):
        """Finalize the state after animation completes."""
        if self._anim_to == EXPANDED_WIDTH:
            self._switch_to_expanded()
            self.setFixedWidth(EXPANDED_WIDTH)
        else:
            self._switch_to_compact()
            self.setFixedWidth(self._calc_compact_width())
