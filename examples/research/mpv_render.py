from PyQt5.QtCore import Qt, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import QOpenGLWidget, QApplication, QWidget, QHBoxLayout
from PyQt5.QtOpenGL import QGLContext

# HELP: currently, we need import GL module，otherwise it will raise seg fault on Linux(Ubuntu 18.04)
# from OpenGL import GL  # noqa

from feeluown.mpv import MPV, OpenGlCbGetProcAddrFn, MpvRenderContext


def get_proc_addr(_, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    addr = int(glctx.getProcAddress(name.decode('utf-8')))
    return addr


class MpvWidget(QOpenGLWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent=parent)
        self.mpv = MPV(ytdl=True)
        self.ctx = None
        self.get_proc_addr_c = OpenGlCbGetProcAddrFn(get_proc_addr)
        self._window = window

    def initializeGL(self):
        params = {'get_proc_address': self.get_proc_addr_c}
        self.ctx = MpvRenderContext(self.mpv,
                                    'opengl',
                                    opengl_init_params=params)
        self.ctx.update_cb = self.on_update

    def paintGL(self):
        # compatible with HiDPI display
        ratio = self._window.devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        opengl_fbo = {'w': w,
                      'h': h,
                      'fbo': self.defaultFramebufferObject()}
        self.ctx.render(flip_y=True, opengl_fbo=opengl_fbo)

    @pyqtSlot()
    def maybe_update(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.doneCurrent()
        else:
            self.update()

    def on_update(self, ctx=None):
        # maybe_update method should run on the thread that creates the OpenGLContext,
        # which in general is the main thread. QMetaObject.invokeMethod can
        # do this trick.
        QMetaObject.invokeMethod(self, 'maybe_update')

    def on_update_fake(self, ctx=None):
        pass

    def closeEvent(self, _):
        # self.makeCurrent()
        # self.mpv.terminate()
        pass


if __name__ == '__main__':
    import locale, time, threading

    app = QApplication([])
    locale.setlocale(locale.LC_NUMERIC, 'C')
    root = QWidget()
    layout = QHBoxLayout(root)
    p1 = QWidget()
    p2 = QWidget()
    l1 = QHBoxLayout(p1)
    l2 = QHBoxLayout(p2)
    layout.addWidget(p1)
    layout.addWidget(p2)
    root.resize(600, 400)
    root.show()

    widget = MpvWidget(root)
    l1.addWidget(widget)
    widget.show()

    url = 'data/test.webm'
    widget.mpv.play(url)

    def reparent():
        time.sleep(1)
        widget.mpv.pause = True
        l2.addWidget(widget)
        widget.mpv.pause = False

    threading.Thread(target=reparent).start()
    app.exec()
