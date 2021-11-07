from PyQt5.QtCore import QMetaObject, pyqtSlot, QRectF, Qt
from PyQt5.QtGui import QPainter, QColor
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

        self._running_danmaku = [
            (5, 10, '感觉好卡呀，为啥呢，heyheyhey？'),
            (10, 20, '周杰伦不香么？'),
            (17, 10, '帧数不够'),
            (23, 10, '尴尬!'),
        ]

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
        # compatible with HiDPI display
        ratio = self._app.devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        opengl_fbo = {'w': w,
                      'h': h,
                      'fbo': self.defaultFramebufferObject()}
        self.ctx.render(flip_y=True, opengl_fbo=opengl_fbo)

        if self._app.player.current_media:
            pass
            #print(self._app.player.position)
            #from feeluown.gui.helpers import resize_font
            #position = self._app.player.position
            #painter = QPainter(self)
            #painter.save()
            #font = painter.font()
            #pen = painter.pen()
            #pen.setColor(QColor('red'))
            #painter.setPen(pen)
            #resize_font(font, 5)
            #painter.setFont(font)
            #fm = painter.fontMetrics()
            #
            #for danmaku in self._running_danmaku:
            #    start, end, text = danmaku
            #    duration = 15
            #    width = fm.horizontalAdvance(text)
            #    if start < position < start+duration:
            #        x = w - ((position - start) / duration * w)
            #        print(x, position)
            #        painter.drawText(QRectF(x, 0, width, 60), Qt.AlignLeft, text)
            #painter.restore()

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
