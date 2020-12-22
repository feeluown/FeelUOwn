import logging
import inspect
import warnings
from collections import deque
from urllib.parse import urlencode

from PyQt5.QtGui import QKeySequence

from feeluown.utils import aio
from feeluown.utils.router import Router, NotFound
from feeluown.models.uri import resolve, reverse, ResolveFailed, parse_line

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

        必须提供 model 或者 path 其中一个参数，都提供时，以 model 为准。

        Typical usage::

            goto(model=model, path=path, query=xxx)
            goto(uri=uri, query=xxx)
        """
        if query:
            qs = urlencode(query)
        else:
            qs = ''
        try:
            if model is not None:
                if qs:
                    path = (path or '') + '?' + qs
                self._goto_model(model, path)
            else:
                # old code use goto(path=uri)
                uri = uri or path
                if qs:
                    uri = uri + '?' + qs
                if not uri.startswith('fuo://'):
                    warnings.warn(f'browser uri should start with fuo://, {uri}')
                    uri = f'fuo://{uri}'
                self._goto_uri(uri)
        except NotFound:
            self._app.show_msg('-> {uri} ...failed', timeout=1)
        else:
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
            self._goto_uri(uri=uri)
            self._forward_stack.append(self._last_uri)
            self.on_history_changed()

    def forward(self):
        try:
            uri = self._forward_stack.pop()
        except IndexError:
            logger.warning("Can't go forward.")
        else:
            self._goto_uri(uri=uri)
            self._back_stack.append(self._last_uri)
            self.on_history_changed()

    def route(self, rule):
        """路由装饰器 (alpha)"""
        return self.router.route(rule)

    def _goto_uri(self, uri):
        assert uri.startswith('fuo://')
        # see if the uri match the two special cases
        # fuo:///models/<provider>/<ns>/<identifier>
        # fuo://<provider>/<ns>/<identifier>
        if uri.startswith('fuo:///models/') or not uri.startswith('fuo:///'):
            try:
                # FIXME: resolve is temporarily too magic
                model_uri = 'fuo://' + uri[14:]
                model, path = parse_line(model_uri)
                model = resolve(reverse(model))
            except ResolveFailed:
                model = None
                logger.warning(f'invalid browser model uri:{uri}')
            else:
                return self._goto_model(model, path)
        else:
            self._goto(uri, {'app': self._app})

    def _goto_model(self, model, path=''):
        path = path or ''
        base_uri = 'fuo:///models/' + reverse(model)[6:]
        if path:
            uri = f'{base_uri}/{path}'
        else:
            uri = base_uri
        self._goto(uri, {'app': self._app, 'model': model})

    def _goto(self, uri, ctx):
        x = self.router.dispatch(uri, ctx)
        if inspect.iscoroutine(x):
            aio.create_task(x)

        self._last_uri = self.current_uri
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
        from feeluown.gui.pages.search import render as render_search
        from feeluown.gui.pages.player_playlist import render as render_player_playlist
        from feeluown.gui.pages.model import render as render_model

        urlpatterns = [
            ('/models/<provider>/<ns>/<identifier>', render_model),
            ('/colls/<identifier>', self._render_coll),
            ('/search', render_search),
            ('/player_playlist', render_player_playlist),
        ]
        for url, handler in urlpatterns:
            self.route(url)(handler)
