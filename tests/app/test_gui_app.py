from feeluown.collection import CollectionManager
from feeluown.app.gui_app import GuiApp
from feeluown.i18n import t


def test_gui_app_initialize(qtbot, mocker, args, config, noharm):
    # TaskManager must be initialized with asyncio.
    mocker.patch('feeluown.app.app.TaskManager')
    mocker.patch.object(CollectionManager, 'scan')
    app = GuiApp(args, config)
    qtbot.addWidget(app)

    mocker.patch.object(app.live_lyric.sentence_changed, 'connect')
    mocker.patch.object(app, 'about_to_exit')
    app.initialize()


def test_gui_app_initialize_updates_network_status_button_tooltip(
    qtbot, mocker, args, config, noharm
):
    mocker.patch('feeluown.app.app.TaskManager')
    mocker.patch.object(CollectionManager, 'scan')
    mocker.patch('feeluown.gui.components.network_status.detect_proxy')
    from feeluown.gui.components.network_status import detect_proxy
    detect_proxy.return_value = {'http': 'http://user:pass@127.0.0.1:7890'}
    app = GuiApp(args, config)
    qtbot.addWidget(app)

    mocker.patch.object(app.live_lyric.sentence_changed, 'connect')
    mocker.patch.object(app, 'about_to_exit')
    app.initialize()

    assert app.ui.bottom_panel.network_status_button.toolTip() == t(
        "proxy-detected", proxyInfo="http=http://127.0.0.1:7890"
    ) + "\n\n" + t("proxy-click-to-refresh")
