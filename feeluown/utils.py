import logging
import platform
import time
from functools import wraps
from PyQt5.QtGui import QColor


logger = logging.getLogger(__name__)


def parse_ms(ms):
    minute = int(ms / 60000)
    second = int((ms % 60000) / 1000)
    return minute, second


def lighter(color, degree=1, a=255):
    r, g, b = color.red(), color.green(), color.blue()
    r = r + 10 * degree if (r + 10 * degree) < 255 else 255
    g = g + 10 * degree if (g + 10 * degree) < 255 else 255
    b = b + 10 * degree if (b + 10 * degree) < 255 else 255
    return QColor(r, g, b, a)


def darker(color, degree=1, a=255):
    r, g, b = color.red(), color.green(), color.blue()
    r = r - 10 * degree if (r - 10 * degree) > 0 else 0
    g = g - 10 * degree if (g - 10 * degree) > 0 else 0
    b = b - 10 * degree if (b - 10 * degree) > 0 else 0
    return QColor(r, g, b, a)


def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t = time.process_time()
        result = func(*args, **kwargs)
        elapsed_time = time.process_time() - t
        logger.info('function %s executed time: %f s'
                    % (func.__name__, elapsed_time))
        return result
    return wrapper


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
