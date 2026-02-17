from unittest import mock

import pytest

from feeluown.library import (
    Collection,
    CollectionType,
    BriefAlbumModel,
    BriefPlaylistModel,
    BriefSongModel,
    BriefVideoModel,
)
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


class _ProviderWithRecCollections:
    identifier = "fake"

    def rec_list_collections(self, limit=None):
        assert limit == 12
        return [
            Collection(
                name="Quick picks",
                type_=CollectionType.only_songs,
                models=[
                    BriefSongModel(
                        identifier="song-1",
                        source="fake",
                        title="Song 1",
                        artists_name="Artist 1",
                    )
                ],
            ),
            Collection(
                name="Daily mixes",
                type_=CollectionType.only_playlists,
                models=[
                    BriefPlaylistModel(
                        identifier="playlist-1",
                        source="fake",
                        name="Mix 1",
                        creator_name="FUO",
                    )
                ],
            ),
            Collection(
                name="Recommended albums",
                type_=CollectionType.only_albums,
                models=[
                    BriefAlbumModel(
                        identifier="album-1",
                        source="fake",
                        name="Album 1",
                        artists_name="Artist A",
                    )
                ],
            ),
            Collection(
                name="Recommended videos",
                type_=CollectionType.only_videos,
                models=[
                    BriefVideoModel(
                        identifier="video-1",
                        source="fake",
                        title="Video 1",
                        artists_name="Artist A",
                    )
                ],
            ),
        ]


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
    assert not view._recommendation_section.isHidden()
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
    assert view._recommendation_section.isHidden()


@pytest.mark.asyncio
async def test_view_render_collections_panel(qtbot, app_mock):
    app_mock.current_pvd_ui_mgr.get.return_value = mock.Mock(
        provider=_ProviderWithRecCollections()
    )
    app_mock.pvd_ui_mgr.get.return_value = None
    app_mock.fm = mock.Mock(is_active=False)

    view = View(app_mock)
    qtbot.addWidget(view)
    await view.render()

    assert view._playlist_panel is None
    assert not view._recommendation_section.isHidden()
    assert len(view._collection_panels) == 4
    assert [panel.header.text() for panel in view._collection_panels] == [
        "Quick picks",
        "Daily mixes",
        "Recommended albums",
        "Recommended videos",
    ]
    assert view._collection_panels[0].songs_list_view._fixed_row_count == 1
    assert view._collection_panels[1].playlist_list_view._fixed_row_count == 1
    assert view._collection_panels[2].album_list_view._fixed_row_count == 1
    assert view._collection_panels[3].video_list_view._fixed_row_count == 1


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
