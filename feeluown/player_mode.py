import logging

logger = logging.getLogger(__name__)


class PlayerModeManager(object):
    current_mode = None

    def __init__(self, app):
        super().__init__()
        self._app = app

    def enter_mode(self, mode):
        self.current_mode = mode
        self._app.player.change_player_mode_to_other()
        msg = '进入 %s 播放模式' % mode.name
        self._app.message(msg)
        logger.info(msg)
        try:
            mode.load()
        except Exception as e:
            logger.error('enter mode %s failed ' % mode.name)
            logger.error(str(e))

    def exit_to_normal(self):
        if self.current_mode is not None:
            self._app.player.change_player_mode_to_normal()
            try:
                self.current_mode.unload()
            except Exception as e:
                logger.error('exit mode %s failed ' % self.current_mode.name)
                logger.error(str(e))
            self.current_mode = None


class PlayerModeBase(object):
    def __init__(self, app):
        super().__init__()
        self._app = app
        self.player = self._app.player
        self.player.signal_playlist_finished.connect(
            self.on_playlist_finished)

    @property
    def name(self):
        raise NotImplementedError('This should be implemented by subclass')

    def on_playlist_finished(self):
        raise NotImplementedError('This should be implemented by subclass')

    def load(self):
        raise NotImplementedError('This should be implemented by subclass')

    def unload(self):
        self._app.message('退出 %s 播放模式' % self.name)
        self.player.signal_playlist_finished.disconnect(
            self.on_playlist_finished)
