from feeluown.components import SongsTable


class PlaylistTable(SongsTable):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
