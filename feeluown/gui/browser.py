import logging
import inspect
import warnings
from collections import deque
from urllib.parse import urlencode
from typing import Optional, Deque

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
        # The two stack are used to save history
        # TODO: Currently, browser only save the whole page path in history, and the
        # related data such as model is not cached. Caching the data should improve
        # performance.
        self._back_stack: Deque[str] = deque(maxlen=10)
        self._forward_stack: Deque[str] = deque(maxlen=10)
        self.router = Router()  # alpha

        self._last_page: Optional[str] = None
        self.current_page: Optional[str] = None

        #: the value in local_storage must be string,
        # please follow the convention
        self.local_storage = {}

    @property
    def ui(self):
        return self._app.ui

    def goto(self, model=None, path=None, page=None, query=None, uri=None):
        """Goto page

        Relations between different goto function, and `_goto` is
        the real renderer::

                 -> _goto_model_page -> _goto
            goto -> _goto_page -> _goto_model_page -> _goto
                               -> _goto

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
            logger.warning(f'{page} renderer not found')
        else:
            # save history records
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
            assert self._last_page is not None
            self._forward_stack.append(self._last_page)
            self.on_history_changed()

    def forward(self):
        try:
            page = self._forward_stack.pop()
        except IndexError:
            logger.warning("Can't go forward.")
        else:
            self._goto_page(page=page)
            assert self._last_page is not None
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
        """goto model page

        The main difference between model page and other pages is that model page
        has different context. It's context has an extra key `model`.
        """
        path = path or ''
        page = base_page = MODEL_PAGE_PREFIX + reverse(model)[6:]
        if path:
            page = f'{base_page}{path}'
        self._goto(page, {'app': self._app, 'model': model})

    def _goto(self, page, ctx):
        # Do some initialization
        self.ui.toolbar.clear_stacked_widget()
        # To keep backward compat, we add magicbox by default
        self.ui.toolbar.add_stacked_widget(self.ui.magicbox)

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
        coll = self._app.coll_mgr.get(identifier)
        self._app.ui.right_panel.show_collection(coll)

    def on_history_changed(self):
        self.ui.back_btn.setEnabled(self.can_back)
        self.ui.forward_btn.setEnabled(self.can_forward)

    # --------------
    # initialization
    # --------------

    def initialize(self):
        """browser should be initialized after all ui components are created

        1. bind routes with renderer
        """
        from feeluown.gui.pages.search import render as render_search
        from feeluown.gui.pages.model import render as render_model
        from feeluown.gui.pages.coll_mixed import render as render_coll_mixed
        from feeluown.gui.pages.song_explore import render as render_song_explore
        from feeluown.gui.pages.provider_home import render as render_provider_home
        from feeluown.gui.pages.recently_played import render as render_recently_played

        model_prefix = f'{MODEL_PAGE_PREFIX}<provider>'

        async def dummy_render(req, *args, **kwargs):
            warnings.warn(f'This route:{req.rule} will be removed.')

        urlpatterns = [
            (f'{model_prefix}/<ns>/<identifier>', render_model),
            # These routes will be removed in v3.9
            (f'{model_prefix}/songs/<identifier>/similar', dummy_render),
            (f'{model_prefix}/songs/<identifier>/hot_comments', dummy_render),
            (f'{model_prefix}/songs/<identifier>/explore', render_song_explore),
            ('/colls/<identifier>', render_coll_mixed),
            ('/providers/<identifier>', render_provider_home),
            ('/recently_played', render_recently_played),
            ('/search', render_search),
        ]
        for url, renderer in urlpatterns:
            self.route(url)(renderer)
