import pytest
from PyQt5.QtCore import QModelIndex

from feeluown.utils import aio
from feeluown.utils.reader import create_reader
from feeluown.gui.widgets.song_minicard_list import SongMiniCardListModel


@pytest.mark.asyncio
async def test_song_mini_card_list_model_remove_pixmap(qtbot, song):
    async def fetch_cover(*_): return b'image content'
    model = SongMiniCardListModel(create_reader([song]), fetch_cover)
    assert model.rowCount() == 0
    model.fetchMore(QModelIndex())
    await aio.sleep(0.1)
    assert model.rowCount() == 1
    model.get_pixmap_unblocking(song)
    await aio.sleep(0.1)
    assert len(model.pixmaps) == 1
    with qtbot.waitSignal(model.rowsAboutToBeRemoved):
        model.beginRemoveRows(QModelIndex(), 0, 0)
        model._items.pop(0)
        model.endRemoveRows()
    assert len(model.pixmaps) == 0
