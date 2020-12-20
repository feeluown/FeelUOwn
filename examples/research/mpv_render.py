from PyQt5.QtCore import Qt, QMetaObject, pyqtSlot
from PyQt5.QtWidgets import QOpenGLWidget, QApplication
from PyQt5.QtOpenGL import QGLContext

# HELP: currently, we need import GL module，otherwise it will raise seg fault on Linux(Ubuntu 18.04)
from OpenGL import GL  # noqa

from mpv import MPV, _mpv_get_sub_api, _mpv_opengl_cb_set_update_callback, \
        _mpv_opengl_cb_init_gl, OpenGlCbGetProcAddrFn, _mpv_opengl_cb_draw, \
        _mpv_opengl_cb_report_flip, MpvSubApi, OpenGlCbUpdateFn, _mpv_opengl_cb_uninit_gl, \
        MpvRenderContext


def get_proc_addr(_, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    addr = int(glctx.getProcAddress(name.decode('utf-8')))
    return addr


class MpvWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.mpv = MPV(ytdl=True)
        self.ctx = None
        self.get_proc_addr_c = OpenGlCbGetProcAddrFn(get_proc_addr)

    def initializeGL(self):
        params = {'get_proc_address': self.get_proc_addr_c}
        self.ctx = MpvRenderContext(self.mpv,
                                    'opengl',
                                    opengl_init_params=params)
        self.ctx.update_cb = self.on_update

    def paintGL(self):
        # compatible with HiDPI display
        ratio = self.windowHandle().devicePixelRatio()
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
    import locale
    app = QApplication([])
    locale.setlocale(locale.LC_NUMERIC, 'C')
    widget = MpvWidget()
    widget.show()
    url = 'data/test.webm'
    widget.mpv.play(url)
    app.exec()
