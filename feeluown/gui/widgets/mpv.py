from PyQt5.QtCore import QMetaObject, pyqtSlot
from PyQt5.QtOpenGL import QGLContext

from mpv import MpvRenderContext, OpenGlCbGetProcAddrFn

from feeluown.gui.widgets.video import VideoOpenGLWidget


def get_proc_addr(_, name):
    glctx = QGLContext.currentContext()
    if glctx is None:
        return 0
    addr = int(glctx.getProcAddress(name.decode('utf-8')))
    return addr


class MpvOpenGLWidget(VideoOpenGLWidget):
    """Mpv 视频输出窗口

    销毁时，应该调用 shutdown 方法来释放资源。

    该 Widget 是模仿一些 C++ 程序编写而成（详见项目 research 目录下的例子），
    我们对背后的原理不太理解，目前测试是可以正常工作的。

    目前主要的疑问有：

    - [ ] shutdown 方法期望是用来释放资源的，目前的写法不知是否合理？
          应该在什么时候调用 shutdown 方法？
    """

    def __init__(self, app, parent=None):
        super().__init__(app=app, parent=parent)
        self._app = app
        self.mpv = self._app.player._mpv  # noqa
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
        ratio = self._app.devicePixelRatio()
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
        # maybe_update method should run on the thread that creates the
        # OpenGLContext, which in general is the main thread.
        # QMetaObject.invokeMethod can do this trick.
        QMetaObject.invokeMethod(self, 'maybe_update')


# TODO: 实现 MpvEmbeddedWidget
class MpvEmbeddedWidget:
    pass
