import platform
import socket


def parse_ms(ms):
    minute = int(ms / 60000)
    second = int((ms % 60000) / 1000)
    return minute, second


def is_linux():
    if platform.system() == 'Linux':
        return True
    return False


def is_osx():
    if platform.system() == 'Darwin':
        return True
    return False


def is_port_used(port, host='0.0.0.0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rv = sock.connect_ex((host, port))
    return rv == 0
