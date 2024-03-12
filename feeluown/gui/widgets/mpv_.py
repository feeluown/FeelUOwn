import sys
from contextlib import contextmanager

from PyQt5.QtCore import QMetaObject, pyqtSlot, QSize
from PyQt5.QtOpenGL import QGLContext

from feeluown.mpv import (
    MpvRenderContext, OpenGlCbGetProcAddrFn, _mpv_set_property_string
)

from feeluown.gui.widgets.video import VideoOpenGLWidget
from feeluown.gui.helpers import IS_MACOS


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

    def shutdown(self):
        if self.ctx is not None:
            self.ctx.free()
            self.ctx = None

    def paintGL(self):
        # HELP: It seems that `initializeGL` is called by Qt on
        # old version (<= v5.15.2)
        if self.ctx is None:
            self.initializeGL()
            assert self.ctx is not None
        # compatible with HiDPI display
        ratio = self._app.devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        opengl_fbo = {'w': w,
                      'h': h,
                      'fbo': self.defaultFramebufferObject()}
        self.ctx.render(flip_y=True, opengl_fbo=opengl_fbo)

        for gl_painter in self._gl_painters:
            gl_painter.paint(self)

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

    # NOTE(cosven): heightForwidth does not work (tested inside nowplaying_overlay.py)
    def hasHeightForWidth(self) -> bool:
        return bool(self.mpv.width)

    def heightForWidth(self, width: int) -> int:
        if self.mpv.width:
            return width // self.mpv.width * self.mpv.height
        return super().heightForWidth(width)

    def sizeHint(self):
        if self.mpv.width:
            return QSize(self.mpv.width, self.mpv.height)
        return super().sizeHint()

    @contextmanager
    def change_parent(self):
        # on macOS, changing mpv widget parent cause no side effects.
        # on Linux (wayland), it seems changing mpv widget parent may cause segfault,
        # so do some hack to avoid crash.
        if not IS_MACOS:
            self._before_change_mpv_widget_parent()
        try:
            yield
        finally:
            if not IS_MACOS:
                self._after_change_mpv_widget_parent()

    def _before_change_mpv_widget_parent(self):
        """
        According to Qt docs, reparenting an OpenGLWidget will destory the GL context.
        In mpv widget, it calls _mpv_opengl_cb_uninit_gl. After uninit_gl, mpv can't show
        video anymore because video_out is destroyed.

        See mpv mpv_opengl_cb_uninit_gl implementation for more details.
        """
        _mpv_set_property_string(self.mpv.handle, b'vid', b'no')
        self.hide()
        self.shutdown()

    def _after_change_mpv_widget_parent(self):
        """
        To recover the video show, we should reinit gl and reinit video. gl is
        automatically reinited when the mpv_widget do painting. We should
        manually reinit video.

        NOTE(cosven): After some investigation, I found that the API in mpv to
        reinit video_out(maybe video is almost same as video_out)
        is init_best_video_out. Theoretically, sending 'video-reload' command
        will trigger this API. However, we can't run this command
        in our case and I don't know why. Another way to trigger
        the API is to switch track. Changing vid property just switch the track.

        Inpect mpv init_best_video_out caller for more details. You should see
        mp_switch_track_n is one of the entrypoint.

        Note the GL must be re-initialized properly before this function is called.
        Generally, show parent once can trigger the initialization. Otherwise,
        mpv.vid will not be set to 1, and video can not be shown.
        """
        self.show()
        self.repaint()  # force repaint to trigger re-initialization
        _mpv_set_property_string(self.mpv.handle, b'vid', b'1')
        if not bool(self.mpv.vid):
            print('WARNING: video widget is not reconfigured properly', file=sys.stderr)


# TODO: 实现 MpvEmbeddedWidget
class MpvEmbeddedWidget:
    pass
