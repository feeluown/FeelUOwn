import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

from feeluown.gui import tray as tray_module
from feeluown.i18n import t


@pytest.fixture
def lyric_window(qtbot, app_mock):
    window = QWidget()
    qtbot.addWidget(window)
    app_mock.ui.lyric_window = window
    return window


def test_tray_toggles_desktop_lyrics(app_mock, lyric_window, monkeypatch):
    monkeypatch.setattr(tray_module, "IS_MACOS", False)
    tray = tray_module.Tray(app_mock)
    action = next(
        action for action in tray.contextMenu().actions()
        if action.text() == t("tray-desktop-lyrics")
    )

    assert not action.isChecked()
    action.trigger()
    assert lyric_window.isVisible()
    assert action.isChecked()

    lyric_window.close()
    assert not action.isChecked()

    lyric_window.show()
    assert action.isChecked()
    action.trigger()
    assert lyric_window.isHidden()
    app_mock.hide.assert_not_called()
    app_mock.show.assert_not_called()


def test_macos_tray_distinguishes_lyric_activation_from_dock_reopen(
    app_mock, lyric_window, monkeypatch
):
    monkeypatch.setattr(tray_module, "IS_MACOS", True)
    lyric_window.show()
    tray = tray_module.Tray(app_mock)

    tray.on_app_state_changed(Qt.ApplicationState.ApplicationInactive)
    tray.on_app_state_changed(Qt.ApplicationState.ApplicationActive)
    app_mock.show.assert_not_called()
    app_mock.activateWindow.assert_not_called()

    tray.on_app_state_changed(Qt.ApplicationState.ApplicationActive)
    app_mock.show.assert_called_once()
    app_mock.activateWindow.assert_called_once()
