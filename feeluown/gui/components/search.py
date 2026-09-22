from datetime import datetime

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QVBoxLayout,
)

from feeluown.gui.widgets.textbtn import TextButton

from feeluown.library import SearchType
from feeluown.utils.aio import run_afn
from feeluown.gui.components.overlay import AppOverlayContainer, AppOverlayOptions
from feeluown.gui.page_containers.table import TableContainer, Renderer
from feeluown.gui.widgets.img_card_list import ImgCardListDelegate
from feeluown.gui.widgets.songs import SongsTableView, ColumnsMode
from feeluown.gui.base_renderer import TabBarRendererMixin
from feeluown.gui.helpers import (
    BgTransparentMixin,
    unify_scroll_area_style,
    set_widget_bg_transparent,
)
from feeluown.gui.widgets.magicbox import KeySourceIn, KeyType
from feeluown.gui.widgets.header import LargeHeader, MidHeader
from feeluown.gui.widgets.accordion import Accordion
from feeluown.gui.widgets.labels import MessageLabel
from feeluown.utils.reader import create_reader
from feeluown.i18n import t


def _toggle_rows(checked, default_count, table, btn):
    table.set_fixed_row_count(default_count if checked else -1)
    btn.setText(t("show-more") if checked else t("show-less"))


_BTN_MARGIN_BOTTOM = 8
_BTN_MIN_WIDTH = 120


class _BtnRepositionFilter(QObject):
    """Repositions a floating button at the bottom-center of a parent widget."""

    def __init__(self, btn, parent_widget):
        super().__init__()
        self._btn = btn
        self._pw = parent_widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self._reposition()
        return False

    def reposition(self):
        btn_hint = self._btn.sizeHint()
        btn_w = max(btn_hint.width(), _BTN_MIN_WIDTH)
        btn_h = btn_hint.height()
        w = self._pw.width()
        h = self._pw.height()
        x = max(0, (w - btn_w) // 2)
        y = max(0, h - btn_h - _BTN_MARGIN_BOTTOM)
        self._btn.move(x, y)


_ACTIVE_TABLE_ATTR = {
    "songs": "songs_table",
    "albums": "albums_table",
    "artists": "artists_table",
    "playlists": "playlists_table",
    "videos": "videos_table",
}


Tabs = [
    (t("track"), SearchType.so),
    (t("album"), SearchType.al),
    (t("musician"), SearchType.ar),
    (t("playlist"), SearchType.pl),
    (t("video"), SearchType.vi),
]


def get_tab_idx(search_type):
    for i, tab in enumerate(Tabs):
        if tab[1] == search_type:
            return i
    raise ValueError("unknown search type")


def create_search_result_view(app, song):
    q = f"{song.title} {song.artists_name}"
    body = SearchResultView(app, transparent_bg=False)
    view = AppOverlayContainer(
        app,
        body,
        parent=app,
        options=AppOverlayOptions(adhoc=True),
    )

    source_in = app.browser.local_storage.get(KeySourceIn, None)
    run_afn(body.search_and_render, q, SearchType.so, source_in)
    return view


class SearchResultView(QScrollArea):
    """
    Usage:
        view = SearchResultView(app)
        await view.search_and_render(q, search_type, source_in)
    """

    def __init__(self, app, transparent_bg=True, parent=None):
        super().__init__(parent=parent)

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        unify_scroll_area_style(self)
        if transparent_bg:
            set_widget_bg_transparent(self)

        self.body = Body(app)
        self.setWidget(self.body)

    def fillable_bg_height(self):
        """Implement VFillableBg protocol"""
        return self.body.height() - self.body.accordion.height()

    async def search_and_render(self, q, search_type, source_in):
        await self.body.search_and_render(q, search_type, source_in)


class Body(QFrame, BgTransparentMixin):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        self._app = app

        self.title = LargeHeader()
        self.hint = MessageLabel()
        self.accordion = Accordion()
        self._reposition_filters = []

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 0, 20, 0)
        self._layout.setSpacing(0)
        self._layout.addSpacing(30)
        self._layout.addWidget(self.title)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.hint)
        self._layout.addSpacing(10)
        self._layout.addWidget(self.accordion)
        self._layout.addStretch(0)

    async def search_and_render(self, q, search_type, source_in):
        # pylint: disable=too-many-locals,too-many-statements
        view = self
        app = self._app

        self.title.setText(t("track-search", keyword=q))

        tab_index = get_tab_idx(search_type)
        succeed = 0
        start = datetime.now()
        self._reposition_filters.clear()
        if source_in is not None:
            source_count = len(source_in)
        else:
            source_count = len(app.library.list())
        hint_msgs = [t("track-searching", providerCount=source_count)]
        view.hint.show_msg("\n".join(hint_msgs))
        async for result in app.library.a_search(
            q, type_in=search_type, source_in=source_in, return_err=True
        ):
            if result.err_msg:
                hint_msgs.append(
                    t(
                        "track-search-error",
                        providerName=result.source,
                        errorMessage=result.err_msg,
                    )
                )
                view.hint.show_msg("\n".join(hint_msgs))
                continue

            table_container = TableContainer(app, view.accordion)
            table_container.layout().setContentsMargins(0, 0, 0, 0)

            renderer = SearchResultRenderer(q, tab_index, source_in=source_in)
            await table_container.set_renderer(renderer)
            _, search_type, attrname, show_handler = renderer.tabs[tab_index]

            # Find the active table and set its fixed row count.
            active_table = getattr(
                table_container, _ACTIVE_TABLE_ATTR[attrname]
            )
            if isinstance(active_table, SongsTableView):
                default_count = 8
                active_table.set_fixed_row_count(default_count)
                active_table.set_row_height(
                    active_table.verticalHeader().defaultSectionSize()
                )
            else:
                default_count = 2
                delegate = active_table.itemDelegate()
                if isinstance(delegate, ImgCardListDelegate):
                    active_table.set_fixed_row_count(default_count)
                    delegate.update_settings("card_min_width", 140)

            objects = getattr(result, attrname) or []
            if not objects:  # Result is empty.
                hint_msgs.append(
                    t("track-search-result-empty", providerName=result.source)
                )
                view.hint.show_msg("\n".join(hint_msgs))
                continue

            succeed += 1
            if search_type is SearchType.so:
                show_handler(  # type: ignore[operator]
                    create_reader(objects), columns_mode=ColumnsMode.playlist
                )
            else:
                show_handler(create_reader(objects))  # type: ignore[operator]
            source = objects[0].source
            provider = app.library.get(source)
            provider_name = provider.name

            header_label = MidHeader(provider_name)

            expand_btn = TextButton(t("show-more"))
            expand_btn.setCheckable(True)
            expand_btn.setChecked(True)
            expand_btn.setStyleSheet(
                "QPushButton {"
                f"  min-width: {_BTN_MIN_WIDTH}px;"
                "  border: 1px solid palette(mid);"
                "  border-radius: 4px;"
                "  padding: 4px 16px;"
                "  background: palette(window);"
                "  color: palette(text);"
                "}"
                "QPushButton:hover {"
                "  border-color: palette(foreground);"
                "}"
            )
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(6)
            shadow.setOffset(0, 1)
            shadow.setColor(QColor(0, 0, 0, 40))
            expand_btn.setGraphicsEffect(shadow)
            content_widget = QFrame()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            content_layout.addWidget(table_container)

            expand_btn.setParent(active_table)
            expand_btn.raise_()
            btn_filter = _BtnRepositionFilter(expand_btn, active_table)
            btn_filter.setParent(active_table)
            active_table.installEventFilter(btn_filter)
            self._reposition_filters.append(btn_filter)

            def _on_toggle(checked, tbl=active_table, count=default_count,
                           btn=expand_btn, f=btn_filter):
                _toggle_rows(checked, count, tbl, btn)
                f.reposition()

            expand_btn.toggled.connect(_on_toggle)
            btn_filter.reposition()

            view.accordion.add_section(
                header_label, content_widget, 6, 12
            )
            renderer.meta_widget.hide()
            renderer.toolbar.hide()
        time_cost = (datetime.now() - start).total_seconds()
        hint_msgs.pop(0)
        hint_msgs.insert(
            0,
            t("track-search-done", resultCount=succeed, timeCost=time_cost),
        )
        view.hint.show_msg("\n".join(hint_msgs))


class SearchResultRenderer(Renderer, TabBarRendererMixin):
    def __init__(self, q, tab_index, source_in=None):
        self.q = q
        self.tab_index = tab_index
        self.source_in = source_in

        self.tabs = [
            (*Tabs[0], "songs", self.show_songs),
            (*Tabs[1], "albums", self.show_albums),
            (*Tabs[2], "artists", self.show_artists),
            (*Tabs[3], "playlists", self.show_playlists),
            (*Tabs[4], "videos", self.show_videos),
        ]

    async def render(self):
        self.render_tab_bar()

    def render_by_tab_index(self, tab_index):
        search_type = self.tabs[tab_index][1]
        self._app.browser.local_storage[KeyType] = search_type.value
        query = {"q": self.q, "type": search_type.value}
        source_in = self._app.browser.local_storage.get(KeySourceIn, None)
        if source_in is not None:
            query["source_in"] = source_in
        self._app.browser.goto(page="/search", query=query)
