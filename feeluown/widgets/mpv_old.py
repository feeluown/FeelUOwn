from PyQt5.QtCore import QMetaObject, pyqtSlot
from PyQt5.QtOpenGL import QGLContext

# HELP: 需要 import GL 模块，否则在 Linux(Ubuntu 18.04) 下会出现 seg fault
from OpenGL import GL  # noqa

from mpv_old import _mpv_get_sub_api, _mpv_opengl_cb_set_update_callback, \
        _mpv_opengl_cb_init_gl, OpenGlCbGetProcAddrFn, _mpv_opengl_cb_draw, \
        _mpv_opengl_cb_report_flip, MpvSubApi, OpenGlCbUpdateFn, _mpv_opengl_cb_uninit_gl

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
        self.mpv_gl = _mpv_get_sub_api(app.player._mpv.handle,
                                       MpvSubApi.MPV_SUB_API_OPENGL_CB)
        self.on_update_c = OpenGlCbUpdateFn(self.on_update)
        self.on_update_fake_c = OpenGlCbUpdateFn(self.on_update_fake)
        self.get_proc_addr_c = OpenGlCbGetProcAddrFn(get_proc_addr)
        self.frameSwapped.connect(self.swapped)

        self._mpv_gl_inited = False

    def shutdown(self):
        if self._mpv_gl_inited:
            self.makeCurrent()
            if self.mpv_gl:
                _mpv_opengl_cb_set_update_callback(
                    self.mpv_gl, self.on_update_fake_c, None)
            _mpv_opengl_cb_uninit_gl(self.mpv_gl)
            self.doneCurrent()

    def initializeGL(self):
        _mpv_opengl_cb_init_gl(self.mpv_gl, None, self.get_proc_addr_c, None)
        _mpv_opengl_cb_set_update_callback(self.mpv_gl, self.on_update_c, None)
        self._mpv_gl_inited = True
        self.context().aboutToBeDestroyed.connect(self.shutdown)

    def paintGL(self):
        # compatible with HiDPI display
        ratio = self.context().screen().devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        _mpv_opengl_cb_draw(self.mpv_gl, self.defaultFramebufferObject(), w, -h)

    @pyqtSlot()
    def maybe_update(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.swapped()
            self.doneCurrent()
        else:
            self.update()

    def on_update(self, ctx=None):
        # HELP: maybeUpdate 中的部分逻辑需要在主线程中执行，
        # 而 QMetaObject.invokeMethod 似乎正好可以达到这个目标。
        # 我们将 maybe_update 标记为 pyqtSlot，这样才能正确的 invoke。
        QMetaObject.invokeMethod(self, 'maybe_update')

    def on_update_fake(self, ctx=None):
        pass

    def swapped(self):
        _mpv_opengl_cb_report_flip(self.mpv_gl, 0)

    def closeEvent(self, _):
        self.shutdown()


# TODO: 实现 MpvEmbeddedWidget
class MpvEmbeddedWidget:
    pass
