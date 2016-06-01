import asyncio
import logging
import socketserver

logger = logging.getLogger(__name__)


class Server(object):
    def __init__(self, app):
        super().__init__()
        self._app = app

    def run(self):
        host = '0.0.0.0'
        port = 8000
        try:
            self.server = socketserver.UDPServer((host, port), Handler)
        except OSError:
            logger.error('udp %d port already in use' % port)
            return

        self.server.app = self._app
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
            self.server.app.player.play()
        elif command == 'pause':
            self.server.app.player.pause()
        elif command == 'next':
            self.server.app.player.play_next()
        elif command == 'previous':
            self.server.app.player.play_last()
        else:
            logger.warning('command not found: %s' % command)
