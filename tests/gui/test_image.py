from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from feeluown.gui.image import ImgManager
from feeluown.media import Media, MediaType


@pytest.mark.asyncio
async def test_img_mgr_get_uses_media_network_options(tmp_path):
    app_mock = MagicMock()
    app_mock.request.get.return_value = SimpleNamespace(content=b"img-bytes")
    img_mgr = ImgManager(app_mock)
    img_mgr.cache.get = MagicMock(return_value=None)
    img_mgr.cache.create = MagicMock(return_value=str(tmp_path / "img.cache"))
    img_mgr.save = MagicMock()

    media = Media(
        "https://img.example.com/a.jpg",
        MediaType.image,
        http_headers={"User-Agent": "fuo-test"},
        http_proxy="http://127.0.0.1:7890",
    )
    content = await img_mgr.get(media, "img-uid")

    assert content == b"img-bytes"
    app_mock.request.get.assert_called_once_with(
        "https://img.example.com/a.jpg",
        headers={"User-Agent": "fuo-test"},
        proxies={
            "http": "http://127.0.0.1:7890",
            "https": "http://127.0.0.1:7890",
        },
    )
