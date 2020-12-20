import logging
import selectors
import socket
from threading import Thread, Event

logger = logging.getLogger(__name__)


class TcpServer(object):
    """A simple TCP server (threading version)

    There is a better implemented ThreadingTCPServer in stdlib, however,
    I just want to reinvent the wheel.

    Happy hacking.

    >>> import time
    >>> from threading import Thread
    >>> def handle(conn, addr, *args): pass
    >>> server = TcpServer(handle_func=handle, host='0.0.0.0', port=33333)
    >>> Thread(target=server.run).start()
    >>> time.sleep(1)
    >>> server.close()
    """
    def __init__(self, host, port, handle_func):
        self.host = host
        self.port = port
        self.handle_func = handle_func

        self._sock = None
        self._close_event = Event()

    def run(self, *args, **kwargs):
        # TODO: enable TCP_QUICKACK?
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen()
        logger.debug('Tcp server running at %s:%d' % (self.host, self.port))
        self._sock = sock
        # TODO: choose a better selector?
        with selectors.DefaultSelector() as sel:
            # NOTE: use selector timeout and server status flag(threading.Event)
            # to make tcp server stoppable
            sel.register(self._sock, selectors.EVENT_READ)
            while not self._close_event.is_set():
                # TODO: better default interval settings?
                ready = sel.select(0.5)
                if not ready:
                    continue
                try:
                    conn, addr = sock.accept()
                except OSError:  # sock is closed
                    logger.debug('Tcp server is closed.')
                    break
                except ConnectionError as e:
                    logger.warning(e)
                    break
                else:
                    logger.debug('%s:%d connected.' % addr)
                    Thread(target=self.handle_func, args=(conn, addr, *args),
                           kwargs=kwargs, name='TcpClientThread').start()
            logger.debug('Tcp server is stopped.')

    def close(self):
        logger.debug('Closing tcp server: %s:%d' % (self.host, self.port))
        if self._sock is not None:
            self._sock.close()
        self._close_event.set()
        logger.debug('Tcp server closed, it will be stopped in 0.5 seconds.')


if __name__ == '__main__':
    import time
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    def func(conn, addr, *args):
        conn.send(b'You are connected.\n')
        conn.send(b'Will close connection in 1 second.\n')
        time.sleep(1)
        f = conn.recv(1024)
        if f == b'close\n':
            conn.close()
            server.close()

    server = TcpServer('0.0.0.0', 33334, handle_func=func)
    server.run()
