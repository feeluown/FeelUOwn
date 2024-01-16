import pytest

from feeluown.library import BriefArtistModel, BriefAlbumModel, SongModel, \
    PlaylistModel
from feeluown.utils.router import Request
from feeluown.gui.pages.model import render as render_model
from feeluown.gui.pages.song_explore import render as render_song_explore
from feeluown.gui.page_containers.table import TableContainer
from feeluown.gui.uimain.page_view import RightPanel


@pytest.fixture
def guiapp(qtbot, app_mock, library):
    tc = TableContainer(app_mock)
    rp = RightPanel(app_mock)
    app_mock.library = library
    app_mock.ui.table_container = tc
    app_mock.ui.right_panel = rp
    qtbot.addWidget(tc)
    qtbot.addWidget(rp)
    return app_mock


@pytest.mark.asyncio
async def test_render_artist_v2(guiapp, ekaf_provider, ekaf_artist0, ):
    artistv2 = BriefArtistModel(source=ekaf_provider.identifier,
                                identifier=ekaf_artist0.identifier)
    ctx = {'model': artistv2, 'app': guiapp}
    req = Request('', '', {}, {}, ctx)
    # Should render without occur.
    await render_model(req)


@pytest.mark.asyncio
async def test_render_album_v2(guiapp, ekaf_provider, ekaf_album0, ):
    albumv2 = BriefAlbumModel(source=ekaf_provider.identifier,
                              identifier=ekaf_album0.identifier)
    ctx = {'model': albumv2, 'app': guiapp}
    req = Request('', '', {}, {}, ctx)
    # Should render without occur.
    await render_model(req)


@pytest.mark.asyncio
async def test_render_song_v2(guiapp, ekaf_provider):
    song = SongModel(source=ekaf_provider.identifier,
                     identifier='0',
                     title='',
                     album=None,
                     artists=[],
                     duration=0)
    ctx = {'model': song, 'app': guiapp}
    req = Request('', '', {}, {}, ctx)
    # No error should occur.
    await render_song_explore(req)


@pytest.mark.asyncio
async def test_render_song_v2_with_non_exists_album(guiapp, ekaf_provider):
    """
    When the album does not exist, the rendering process should succeed.
    This test case tests that every exceptions, which raised by library, should
    be correctly catched.
    """
    song = SongModel(source=ekaf_provider.identifier,
                     identifier='0',
                     title='',
                     album=BriefAlbumModel(source=ekaf_provider.identifier,
                                           identifier='not_exist'),
                     artists=[],
                     duration=0)
    ctx = {'model': song, 'app': guiapp}
    req = Request('', '', {}, {}, ctx)
    # No error should occur.
    await render_song_explore(req)


@pytest.mark.asyncio
async def test_render_playlist_v2(guiapp, ekaf_provider, mocker):
    mock_error = mocker.patch('feeluown.gui.pages.model.render_error_message')
    playlist = PlaylistModel(
        source=ekaf_provider.identifier,
        identifier='does_not_exist',
        name='',
        cover='',
        description=''
    )
    ctx = {'model': playlist, 'app': guiapp}
    req = Request('', '', {}, {}, ctx)

    # ekaf_provider does not support create songs reader for playlist currently.
    await render_model(req)
    assert mock_error.called
