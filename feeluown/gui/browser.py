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


MODEL_PAGE_PREFIX = '/models/'


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

        self._last_page = None
        self.current_page = None

        #: the value in local_storage must be string,
        # please follow the convention
        self.local_storage = {}

        self._app.hotkey_mgr.register([QKeySequence.Back], self.back)
        self._app.hotkey_mgr.register([QKeySequence.Forward], self.forward)

    @property
    def ui(self):
        return self._app.ui

    def goto(self, model=None, path=None, page=None, query=None,
             uri=None):
        """goto page

        Typical usage::

            goto(model=model, path=path, query=xxx)
            goto(page=page, query=xxx)

        Wrong usage::

            goto(path=page, query=xxx)
        """
        # backward compact: old code use goto(uri=page)
        if uri is not None:
            warnings.warn('please use parameter page', DeprecationWarning)
            page = page or uri

        qs = urlencode(query) if query else ''

        try:
            if model is not None:
                if qs:
                    path = (path or '') + '?' + qs
                self._goto_model_page(model, path)
            else:
                # backward compat: old code use goto(path=page) wrongly
                if path is not None:
                    warnings.warn('please use parameter page')
                page = page or path
                if qs:
                    page = page + '?' + qs
                self._goto_page(page)
        except NotFound:
            self._app.show_msg('-> {page} ...failed', timeout=1)
        else:
            if self._last_page is not None and self._last_page != self.current_page:
                self._back_stack.append(self._last_page)
            self._forward_stack.clear()
            self.on_history_changed()

    def back(self):
        try:
            page = self._back_stack.pop()
        except IndexError:
            logger.warning("Can't go back.")
        else:
            self._goto_page(page=page)
            self._forward_stack.append(self._last_page)
            self.on_history_changed()

    def forward(self):
        try:
            page = self._forward_stack.pop()
        except IndexError:
            logger.warning("Can't go forward.")
        else:
            self._goto_page(page=page)
            self._back_stack.append(self._last_page)
            self.on_history_changed()

    def route(self, rule):
        """路由装饰器 (alpha)"""
        return self.router.route(rule)

    def _goto_page(self, page):
        # see if the page match the two special cases
        if page.startswith(MODEL_PAGE_PREFIX):
            try:
                # FIXME: resolve is temporarily too magic
                uri = 'fuo://' + page[len(MODEL_PAGE_PREFIX):]
                model, path = parse_line(uri)
                model = resolve(reverse(model))
            except ResolveFailed:
                model = None
                logger.warning(f'invalid model page:{page}')
            else:
                return self._goto_model_page(model, path)
        else:
            self._goto(page, {'app': self._app})

    def _goto_model_page(self, model, path=''):
        path = path or ''
        page = base_page = '/models/' + reverse(model)[6:]
        if path:
            page = f'{base_page}/{path}'
        self._goto(page, {'app': self._app, 'model': model})

    def _goto(self, page, ctx):
        x = self.router.dispatch(page, ctx)
        if inspect.iscoroutine(x):
            aio.create_task(x)

        self._last_page = self.current_page
        self.current_page = page

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
