import asyncio
import logging
import socketserver

from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class Server(QObject):
    play_signal = pyqtSignal()
    pause_signal = pyqtSignal()
    play_or_pause_signal = pyqtSignal()
    play_next_signal = pyqtSignal()
    play_previous_signal = pyqtSignal()

    def __init__(self, app):
        super().__init__(app)
        self._app = app

        self.play_signal.connect(self._app.player.play)
        self.pause_signal.connect(self._app.player.pause)
        self.play_or_pause_signal.connect(self._app.player.play_or_pause)
        self.play_next_signal.connect(self._app.player.play_next)
        self.play_previous_signal.connect(self._app.player.play_last)

    def run(self):
        host = '0.0.0.0'
        port = 8000
        try:
            self.server = socketserver.UDPServer((host, port), Handler)
        except OSError:
            logger.error('udp %d port already in use' % port)
            return

        self.server.ctrl = self
        event_loop = asyncio.get_event_loop()
        event_loop.run_in_executor(None,
                                   self.server.serve_forever)
        logger.info('server run in %d' % port)
        self._app.message('命令行服务运行于 %d 端口' % port)

    def stop(self):
        self.server.shutdown()


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request[0].strip()
        logger.info('{} send: {}'.format(self.client_address[0], self.data))
        command = self.data.decode('utf-8')
        if command == 'play':
            self.server.ctrl.play_signal.emit()
        elif command == 'pause':
            self.server.ctrl.pause_signal.emit()
        elif command == 'next':
            self.server.ctrl.play_next_signal.emit()
        elif command == 'previous':
            self.server.ctrl.play_previous_signal.emit()
        elif command == 'play_pause':
            self.server.ctrl.play_or_pause_signal.emit()
        else:
            logger.warning('command not found: %s' % command)
