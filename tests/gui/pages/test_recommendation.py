from unittest import mock

import pytest

from PyQt6.QtWidgets import QScrollArea

from feeluown.utils.router import Request
from feeluown.gui.page_containers.scroll_area import ScrollArea
from feeluown.gui.pages.recommendation import View, render
from feeluown.i18n import t


class _ProviderWithRecPlaylists:
    identifier = "fake"

    def rec_list_daily_playlists(self):
        return []


class _ProviderWithoutRecPlaylists:
    identifier = "fake"


@pytest.mark.asyncio
async def test_view_render_show_playlist_panel(qtbot, app_mock):
    app_mock.current_pvd_ui_mgr.get.return_value = mock.Mock(
        provider=_ProviderWithRecPlaylists()
    )
    app_mock.pvd_ui_mgr.get.return_value = None
    app_mock.browser.goto = mock.Mock()
    app_mock.fm = mock.Mock(is_active=False)

    view = View(app_mock)
    qtbot.addWidget(view)
    await view.render()

    assert view._playlist_panel is not None
    assert not view._playlist_section.isHidden()
    assert view._playlist_panel.icon_label.isHidden()
    assert (
        view._playlist_panel.header.text() == t("music-customized-recommendation")
    )


@pytest.mark.asyncio
async def test_view_render_hide_playlist_panel_for_unsupported_provider(
    qtbot, app_mock
):
    app_mock.current_pvd_ui_mgr.get.return_value = mock.Mock(
        provider=_ProviderWithoutRecPlaylists()
    )
    app_mock.fm = mock.Mock(is_active=False)

    view = View(app_mock)
    qtbot.addWidget(view)
    await view.render()

    assert view._playlist_panel is None
    assert view._playlist_section.isHidden()


@pytest.mark.asyncio
async def test_render_set_scroll_area_body(app_mock):
    app_mock.current_pvd_ui_mgr.get.return_value = mock.Mock(
        provider=_ProviderWithoutRecPlaylists()
    )
    app_mock.fm = mock.Mock(is_active=False)
    req = Request("", "", {}, {}, {"app": app_mock})

    await render(req)

    args, _ = app_mock.ui.right_panel.set_body.call_args
    assert isinstance(args[0], ScrollArea)


def test_action_buttons_wrap_adaptively(qtbot, app_mock):
    app_mock.fm = mock.Mock(is_active=False)
    view = View(app_mock)
    qtbot.addWidget(view)

    view.resize(1200, 600)
    view._reflow_action_buttons()
    assert view._action_cols == 4

    view.resize(520, 600)
    view._reflow_action_buttons()
    assert view._action_cols == 2
    assert view._action_layout.itemAtPosition(0, 0).widget() is view.daily_songs_btn
    assert view._action_layout.itemAtPosition(0, 1).widget() is view.rank_btn
    assert view._action_layout.itemAtPosition(1, 0).widget() is view.heart_radar_btn
    assert view._action_layout.itemAtPosition(1, 1).widget() is view.dislike_btn

    view.resize(360, 600)
    view._reflow_action_buttons()
    assert view._action_cols == 1


def test_action_buttons_wrap_with_scrollarea_parent(qtbot, app_mock):
    app_mock.fm = mock.Mock(is_active=False)
    view = View(app_mock)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(view)
    qtbot.addWidget(scroll)
    scroll.show()

    scroll.resize(1200, 600)
    qtbot.wait(10)
    assert view._action_cols == 4

    scroll.resize(520, 600)
    qtbot.wait(10)
    assert view._action_cols == 2
    # The horizontal scrollbar should not be needed after reflow.
    assert scroll.horizontalScrollBar().maximum() == 0
