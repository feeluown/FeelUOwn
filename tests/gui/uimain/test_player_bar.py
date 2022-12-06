import pytest

from tests.helpers import cannot_run_qt_test
from feeluown.gui.uimain.player_bar import PlayerControlPanel
from feeluown.media import Media


@pytest.mark.skipif(cannot_run_qt_test, reason='this is a qt testcase')
def test_show_bitrate(qtbot, app_mock, mocker):
    app_mock.player.current_media = Media('http://', bitrate=100)
    w = PlayerControlPanel(app_mock)
    qtbot.addWidget(w)
    metadata = {'title': 'xx'}
    w.on_metadata_changed(metadata)
    assert '100kbps' in w.song_source_label.text()
