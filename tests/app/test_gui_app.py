from feeluown.app.gui_app import GuiApp


def test_gui_app(qtbot, mocker, args, config, no_player):
    mocker.patch('feeluown.app.app.TaskManager')
    app = GuiApp(args, config)
    qtbot.addWidget(app)
