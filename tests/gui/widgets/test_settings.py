from feeluown.gui.components.network_status import NetworkStatusButton
from feeluown.gui.widgets.settings import AISettings, SettingsDialog


def test_settings_dialog_has_network_status_button(qtbot, app_mock):
    app_mock.browser.local_storage.get.return_value = None
    app_mock.library.list.return_value = []
    app_mock.config.AI_RADIO_PROMPT = ""

    dialog = SettingsDialog(app_mock)
    qtbot.addWidget(dialog)

    assert isinstance(dialog.network_status_button, NetworkStatusButton)


def test_bottom_panel_does_not_show_network_status_button(qtbot, app_mock):
    from feeluown.gui.uimain.toolbar import BottomPanel

    panel = BottomPanel(app_mock)
    qtbot.addWidget(panel)

    assert not hasattr(panel, "network_status_button")


def test_ai_settings_prompt_editor_is_compact(qtbot, app_mock):
    app_mock.config.AI_RADIO_PROMPT = ""

    settings = AISettings(app_mock)
    qtbot.addWidget(settings)

    assert settings._prompt_editor.maximumHeight() == 96
