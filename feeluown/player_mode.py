class PlayerModeManager(object):
    current_mode = None

    def __init__(self, app):
        super().__init__()
        self._app = app

    def enter_mode(self, mode):
        self._app.player.change_player_mode_to_other()

    def exit_to_normal(self):
        self._app.player.change_player_mode_to_other()
