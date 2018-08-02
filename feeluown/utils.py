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


def emit_requests_progress(response, signal=None):
    content = bytes()
    total_size = response.headers.get('content-length')
    if total_size is None:
        content = response.content
        return content
    else:
        total_size = int(total_size)
        bytes_so_far = 0

        for chunk in response.iter_content(102400):
            content += chunk
            bytes_so_far += len(chunk)
            progress = round(bytes_so_far * 1.0 / total_size * 100)
            if signal is not None:
                signal.emit(progress)
        return content


def is_port_used(port, host='0.0.0.0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rv = sock.connect_ex((host, port))
    return rv == 0
