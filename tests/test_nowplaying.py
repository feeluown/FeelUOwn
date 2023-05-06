import pytest

from feeluown.nowplaying import get_service_cls
from .helpers import is_macos, aio_waitfor_simple_tasks


@pytest.mark.skipif(not is_macos, reason='only test on macos')
@pytest.mark.asyncio
async def test_macos_update_song_pic(app_mock):
    service = get_service_cls()(app_mock)
    service.update_song_metadata({})
    await aio_waitfor_simple_tasks()
    assert app_mock.img_mgr.get.called
