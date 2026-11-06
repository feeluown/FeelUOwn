import logging
import inspect
import os
import sys
import warnings
from collections import deque
from urllib.parse import urlencode
from typing import Optional, Deque

from feeluown.utils import aio
from feeluown.utils.router import Router, NotFound
from feeluown.library import resolve, reverse, ResolveFailed, parse_line

logger = logging.getLogger(__name__)


def _is_test_env():
    """Whether running under pytest.

    Lazy page imports defer Qt module imports to first navigation, which
    happens inside event processing on some runners and has caused
    offscreen segfaults (ubuntu py3.10). Eager-load in tests for
    deterministic behavior; keep lazy loading in production for startup.

    NOTE: only check pytest markers (PYTEST_CURRENT_TEST / sys.modules),
    NOT TEST_ENV, because integration tests run `fuo` as a subprocess
    with TEST_ENV=travis inherited, and that subprocess must paint
    normally.
    """
    return (
        os.getenv('PYTEST_CURRENT_TEST') is not None
        or 'pytest' in sys.modules
    )


MODEL_PAGE_PREFIX = "/models/"


class Browser:
    """GUI Page Management Center

    Compare feeluown to a browser: magicbox is the search box,
    RightPanel is the main browser area.
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
            warnings.warn("please use parameter page", DeprecationWarning)
            page = page or uri

        qs = urlencode(query) if query else ""

        try:
            if model is not None:
                if qs:
                    path = (path or "") + "?" + qs
                self._goto_model_page(model, path)
            else:
                # backward compat: old code use goto(path=page) wrongly
                if path is not None:
                    warnings.warn("please use parameter page")
                page = page or path
                if qs:
                    page = page + "?" + qs
                self._goto_page(page)
        except NotFound:
            logger.warning(f"{page} renderer not found")
        except Exception as e:
            # Lazy page modules are imported on first navigation; an import
            # failure used to fail fast at initialize() and now surfaces
            # here. Programming errors in renderers must stay loud in DEBUG
            # (re-raised); otherwise log, notify, and leave the current
            # page/history untouched.
            self._report_nav_error('navigate', page, e)
            return
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
            try:
                self._goto_page(page=page)
            except Exception as e:
                self._report_nav_error('navigate back to', page, e)
                return
            assert self._last_page is not None
            self._forward_stack.append(self._last_page)
            self.on_history_changed()

    def forward(self):
        try:
            page = self._forward_stack.pop()
        except IndexError:
            logger.warning("Can't go forward.")
        else:
            try:
                self._goto_page(page=page)
            except Exception as e:
                self._report_nav_error('navigate forward to', page, e)
                return
            assert self._last_page is not None
            self._back_stack.append(self._last_page)
            self.on_history_changed()

    def _report_nav_error(self, action, page, exc):
        """Log + notify a navigation failure; re-raise in DEBUG.

        Import/attribute errors (lazy page load failures) are always handled
        (old behavior failed fast at initialize()). Other renderer bugs are
        handled too, except in DEBUG mode where they are re-raised so tests
        and developers see the loud crash.
        """
        if isinstance(exc, (ImportError, AttributeError)):
            logger.exception(f"Failed to {action} {page}")
        elif getattr(getattr(self._app, 'config', None), 'DEBUG', False) is True:
            raise exc
        else:
            logger.exception(f"Failed to {action} {page}")
        try:
            self._app.show_msg(f"Load page failed: {exc}")
        except Exception:  # noqa
            pass

    def route(self, rule):
        """Routing decorator (alpha)"""
        return self.router.route(rule)

    def _goto_page(self, page):
        # see if the page match the two special cases
        if page.startswith(MODEL_PAGE_PREFIX):
            try:
                # FIXME: resolve is temporarily too magic
                uri = "fuo://" + page[len(MODEL_PAGE_PREFIX) :]
                model, path = parse_line(uri)
                model = resolve(reverse(model))
            except ResolveFailed:
                model = None
                logger.warning(f"invalid model page:{page}")
            else:
                return self._goto_model_page(model, path)
        else:
            self._goto(page, {"app": self._app})

    def _goto_model_page(self, model, path=""):
        """goto model page

        The main difference between model page and other pages is that model page
        has different context. It's context has an extra key `model`.
        """
        path = path or ""
        page = base_page = MODEL_PAGE_PREFIX + reverse(model)[6:]
        if path:
            page = f"{base_page}{path}"
        self._goto(page, {"app": self._app, "model": model})

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

        Only the homepage renderer is imported eagerly since startup
        always navigates to it. All other pages are lazy-loaded on first
        visit to reduce startup import cost (each page pulls Qt widgets,
        provider protocols and components).

        In test/CI environments, import all pages eagerly for
        deterministic behavior (old behavior).
        """
        import importlib

        from feeluown.gui.pages.homepage import render as render_homepage

        if _is_test_env():
            from feeluown.gui.pages.search import render as render_search
            from feeluown.gui.pages.model import render as render_model
            from feeluown.gui.pages.coll_mixed import render as render_coll_mixed
            from feeluown.gui.pages.song_explore import (
                render as render_song_explore,
            )
            from feeluown.gui.pages.provider_home import (
                render as render_provider_home,
            )
            from feeluown.gui.pages.recently_played import (
                render as render_recently_played,
            )
            from feeluown.gui.pages.recommendation import render as render_rec
            from feeluown.gui.pages.recommendation_daily_songs import (
                render as render_rec_daily_songs,
            )
            from feeluown.gui.pages.my_fav import render as render_my_fav
            from feeluown.gui.pages.my_dislike import render as render_my_dislike
            from feeluown.gui.pages.toplist import render as render_toplist

            model_prefix = f"{MODEL_PAGE_PREFIX}<provider>"

            async def dummy_render(req, *args, **kwargs):
                warnings.warn(f"This route:{req.rule} will be removed.")

            urlpatterns = [
                (f"{model_prefix}/<ns>/<identifier>", render_model),
                # These routes will be removed in v3.9
                (f"{model_prefix}/songs/<identifier>/similar", dummy_render),
                (f"{model_prefix}/songs/<identifier>/hot_comments", dummy_render),
                (f"{model_prefix}/songs/<identifier>/explore", render_song_explore),
                ("/colls/<identifier>", render_coll_mixed),
                ("/providers/<identifier>", render_provider_home),
                ("/recently_played", render_recently_played),
                ("/search", render_search),
                ("/rec", render_rec),
                ("/homepage", render_homepage),
                ("/rec/daily_songs", render_rec_daily_songs),
                ("/my_fav", render_my_fav),
                ("/my_dislike", render_my_dislike),
                ("/toplist", render_toplist),
            ]
            for url, renderer in urlpatterns:
                self.route(url)(renderer)
            return

        def _lazy(module_path):
            _cache = {}

            def _render(req, **kwargs):
                mod = _cache.get('mod')
                if mod is None:
                    try:
                        mod = importlib.import_module(module_path)
                    except Exception:
                        # Import errors previously surfaced at initialize();
                        # now they surface on first navigation, so log them
                        # here. goto() only handles NotFound, other errors
                        # propagate to the caller.
                        logger.exception('Failed to load page module %s', module_path)
                        raise
                    _cache['mod'] = mod
                return mod.render(req, **kwargs)
            # Keep a helpful name for debugging/router logs.
            _render.__name__ = f'lazy_{module_path.rsplit(".", 1)[-1]}_render'
            return _render

        model_prefix = f"{MODEL_PAGE_PREFIX}<provider>"

        async def dummy_render(req, *args, **kwargs):
            warnings.warn(f"This route:{req.rule} will be removed.")

        urlpatterns = [
            (f"{model_prefix}/<ns>/<identifier>",
             _lazy('feeluown.gui.pages.model')),
            # These routes will be removed in v3.9
            (f"{model_prefix}/songs/<identifier>/similar", dummy_render),
            (f"{model_prefix}/songs/<identifier>/hot_comments", dummy_render),
            (f"{model_prefix}/songs/<identifier>/explore",
             _lazy('feeluown.gui.pages.song_explore')),
            ("/colls/<identifier>", _lazy('feeluown.gui.pages.coll_mixed')),
            ("/providers/<identifier>",
             _lazy('feeluown.gui.pages.provider_home')),
            ("/recently_played",
             _lazy('feeluown.gui.pages.recently_played')),
            ("/search", _lazy('feeluown.gui.pages.search')),
            ("/rec", _lazy('feeluown.gui.pages.recommendation')),
            ("/homepage", render_homepage),
            ("/rec/daily_songs",
             _lazy('feeluown.gui.pages.recommendation_daily_songs')),
            ("/my_fav", _lazy('feeluown.gui.pages.my_fav')),
            ("/my_dislike", _lazy('feeluown.gui.pages.my_dislike')),
            ("/toplist", _lazy('feeluown.gui.pages.toplist')),
        ]
        for url, renderer in urlpatterns:
            self.route(url)(renderer)
