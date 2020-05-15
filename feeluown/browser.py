import logging
import inspect
import warnings
from collections import deque
from urllib.parse import urlencode

from PyQt5.QtGui import QKeySequence

from fuocore import aio
from fuocore.router import Router, NotFound
from fuocore.models.uri import resolve, reverse, ResolveFailed

logger = logging.getLogger(__name__)


class Browser:
    """GUI 页面管理中心

    将 feeluown 类比为浏览器：magicbox 是搜索框，RightPanel
    部分是浏览器主体。
    """

    def __init__(self, app):
        self._app = app
        # 保存后退、前进历史的两个栈
        self._back_stack = deque(maxlen=10)
        self._forward_stack = deque(maxlen=10)
        self.router = Router()  # alpha

        self._last_uri = None
        self.current_uri = None

        #: the value in local_storage must be string,
        # please follow the convention
        self.local_storage = {}

        self._app.hotkey_mgr.register([QKeySequence.Back], self.back)
        self._app.hotkey_mgr.register([QKeySequence.Forward], self.forward)

    @property
    def ui(self):
        return self._app.ui

    def goto(self, model=None, path=None, uri=None, query=None):
        """跳转到 model 页面或者具体的地址

        必须提供 model 或者 uri 其中一个参数，都提供时，以 model 为准。
        """
        if uri is not None:
            warnings.warn('please use path instead of uri')
        if query:
            qs = urlencode(query)
            uri = (path or uri) + '?' + qs
        self._goto(model, uri)
        if self._last_uri is not None and self._last_uri != self.current_uri:
            self._back_stack.append(self._last_uri)
        self._forward_stack.clear()
        self.on_history_changed()

    def back(self):
        try:
            uri = self._back_stack.pop()
        except IndexError:
            logger.warning("Can't go back.")
        else:
            self._goto(uri=uri)
            self._forward_stack.append(self._last_uri)
            self.on_history_changed()

    def forward(self):
        try:
            uri = self._forward_stack.pop()
        except IndexError:
            logger.warning("Can't go forward.")
        else:
            self._goto(uri=uri)
            self._back_stack.append(self._last_uri)
            self.on_history_changed()

    def route(self, rule):
        """路由装饰器 (alpha)"""
        return self.router.route(rule)

    def _goto(self, model=None, uri=None):
        """真正的跳转逻辑"""
        if model is None:
            try:
                model = resolve(uri)
            except ResolveFailed:
                model = None
        else:
            uri = reverse(model)
        if not uri.startswith('fuo://'):
            uri = 'fuo://' + uri
        with self._app.create_action('-> {}'.format(uri)) as action:
            if model is not None:
                self._render_model(model)
            else:
                try:
                    x = self.router.dispatch(uri, {'app': self._app})
                    if inspect.iscoroutine(x):
                        aio.create_task(x)
                except NotFound:
                    action.failed(f'{uri} not found.')
                    return
        self._last_uri = self.current_uri
        if model is not None:
            self.current_uri = reverse(model)
        else:
            self.current_uri = uri

    @property
    def can_back(self):
        return len(self._back_stack) > 0

    @property
    def can_forward(self):
        return len(self._forward_stack) > 0

    # --------------
    # UI Controllers
    # --------------

    def _render_model(self, model):
        """渲染 model 页面"""
        self._app.ui.right_panel.show_model(model)

    def _render_coll(self, _, identifier):
        coll = self._app.coll_uimgr.get(int(identifier))
        self._app.ui.right_panel.show_collection(coll)

    def on_history_changed(self):
        self.ui.back_btn.setEnabled(self.can_back)
        self.ui.forward_btn.setEnabled(self.can_forward)

    # --------------
    # initialization
    # --------------

    def initialize(self):
        """browser should be initialized after all ui components are created

        1. bind routes with handler
        """
        from feeluown.gui.pages import (
            render_search,
            render_player_playlist,
        )

        urlpatterns = [
            ('/colls/<identifier>', self._render_coll),
            ('/search', render_search),
            ('/player_playlist', render_player_playlist),
        ]
        for url, handler in urlpatterns:
            self.route(url)(handler)
