import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio
from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtGui import QColor, QImage

from feeluown.gui.components.desktop_lyric import DesktopLyricCard
from feeluown.media import Media, MediaType
from feeluown.utils.dispatch import Signal


def _image_bytes(color):
    image = QImage(16, 16, QImage.Format.Format_ARGB32)
    image.fill(QColor(color))
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return bytes(buffer.data())


@pytest_asyncio.fixture
async def lyric_app():
    app = SimpleNamespace(
        player=SimpleNamespace(current_metadata={}, metadata_changed=Signal()),
        live_lyric=SimpleNamespace(
            current_lyrics=(None, None),
            lyrics_changed=Signal(),
            line_changed=Signal(),
        ),
        library=SimpleNamespace(get=Mock(return_value=None)),
        img_mgr=SimpleNamespace(get=AsyncMock(return_value=_image_bytes("red"))),
    )
    Signal.setup_aio_support()
    try:
        yield app
    finally:
        Signal.teardown_aio_support()


@pytest.fixture
def cover_tasks(monkeypatch):
    tasks = []

    def run_cover_task(afn, *args):
        task = asyncio.create_task(afn(*args))
        tasks.append(task)
        return task

    monkeypatch.setattr(
        "feeluown.gui.components.desktop_lyric.run_afn", run_cover_task
    )
    return tasks


@pytest.mark.asyncio
async def test_desktop_lyrics_load_current_provider_cover(
    qtbot, lyric_app, cover_tasks
):
    artwork = "https://example.test/cover.png"
    media = Media(
        artwork,
        MediaType.image,
        http_headers={"Referer": "https://example.test/"},
        http_proxy="http://127.0.0.1:7890",
    )
    provider = SimpleNamespace(img_url_to_media=Mock(return_value=media))
    lyric_app.library.get.return_value = provider
    lyric_app.player.current_metadata = {
        "artwork": artwork, "source": "provider", "uri": "fuo://provider/songs/1"
    }

    card = DesktopLyricCard(lyric_app)
    qtbot.addWidget(card)
    await asyncio.gather(*cover_tasks)

    lyric_app.library.get.assert_called_once_with("provider")
    provider.img_url_to_media.assert_called_once_with(artwork)
    lyric_app.img_mgr.get.assert_awaited_once_with(media, "fuo://provider/songs/1")
    assert card._cover.pixelColor(0, 0) == QColor("red")


@pytest.mark.asyncio
async def test_desktop_lyrics_clear_cover_when_song_has_no_artwork(
    qtbot, lyric_app, cover_tasks
):
    lyric_app.player.current_metadata = {"artwork": "cover"}
    card = DesktopLyricCard(lyric_app)
    qtbot.addWidget(card)
    await asyncio.gather(*cover_tasks)
    assert not card._cover.isNull()

    lyric_app.player.current_metadata = {"title": "No cover"}
    lyric_app.player.metadata_changed.emit(lyric_app.player.current_metadata)
    await Signal.aioqueue.async_q.join()

    assert card._cover.isNull()
    assert lyric_app.img_mgr.get.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement", [
    {"artwork": "new-cover", "source": "new", "uri": "new"},
    {"artwork": "old-cover", "source": "new", "uri": "new"},
    {},
])
async def test_desktop_lyrics_ignore_cover_from_previous_song(
    qtbot, lyric_app, cover_tasks, replacement
):
    previous_cover = asyncio.get_running_loop().create_future()

    async def get_cover(media, uid):
        if uid == "old":
            return await previous_cover
        return _image_bytes("blue")

    lyric_app.img_mgr.get.side_effect = get_cover
    lyric_app.player.current_metadata = {
        "artwork": "old-cover", "source": "old", "uri": "old"
    }
    card = DesktopLyricCard(lyric_app)
    qtbot.addWidget(card)
    await asyncio.sleep(0)

    lyric_app.player.current_metadata = replacement
    lyric_app.player.metadata_changed.emit(replacement)
    await Signal.aioqueue.async_q.join()
    if replacement:
        await cover_tasks[-1]
        assert card._cover.pixelColor(0, 0) == QColor("blue")
    else:
        assert card._cover.isNull()

    previous_cover.set_result(_image_bytes("red"))
    await cover_tasks[0]
    if replacement:
        assert card._cover.pixelColor(0, 0) == QColor("blue")
    else:
        assert card._cover.isNull()


@pytest.mark.asyncio
async def test_desktop_lyrics_keep_plain_background_when_cover_download_fails(
    qtbot, lyric_app, cover_tasks
):
    lyric_app.player.current_metadata = {"artwork": "cover"}
    lyric_app.img_mgr.get.return_value = None
    card = DesktopLyricCard(lyric_app)
    qtbot.addWidget(card)
    await asyncio.gather(*cover_tasks)

    assert card._cover.isNull()
