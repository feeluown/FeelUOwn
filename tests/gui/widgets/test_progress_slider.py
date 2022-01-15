import pytest
from PyQt5.QtWidgets import QAbstractSlider

from feeluown.gui.widgets.progress_slider import ProgressSlider


@pytest.fixture
def mock_update_player(mocker):
    return mocker.patch.object(ProgressSlider, 'maybe_update_player_position')


@pytest.fixture
def slider(qtbot, app_mock):
    slider = ProgressSlider(app_mock)
    app_mock.player.current_media = object()  # An non-empty object.
    app_mock.player.position = 0
    qtbot.addWidget(slider)
    return slider


def test_basics(qtbot, app_mock):
    slider = ProgressSlider(app_mock)
    qtbot.addWidget(slider)


def test_action_is_triggered(slider, mock_update_player):
    slider.triggerAction(QAbstractSlider.SliderPageStepAdd)
    assert mock_update_player.called


def test_maybe_update_player_position(slider):
    slider.maybe_update_player_position(10)

    assert slider._app.player.position == 10
    assert slider._app.player.resume.called


def test_update_total(slider):
    slider.update_total(10)
    assert slider.maximum() == 10


def test_drag_slider(slider, mock_update_player):
    # Simulate the dragging.
    slider.setSliderDown(True)
    slider.setSliderDown(False)
    assert mock_update_player.called


def test_media_changed_during_dragging(qtbot, slider, mock_update_player):
    # Simulate the dragging.
    slider.setSliderDown(True)
    slider._dragging_ctx.is_media_changed = True  # Simulate media changed.
    slider.setSliderDown(False)
    assert not mock_update_player.called


def test_when_player_has_no_media(slider):
    slider._app.player.current_media = None
    slider.triggerAction(QAbstractSlider.SliderPageStepAdd)
    assert not slider._app.player.resume.called
