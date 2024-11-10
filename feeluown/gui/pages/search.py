from feeluown.library import SearchType
from feeluown.utils.router import Request
from feeluown.app.gui_app import GuiApp
from feeluown.gui.components.search import SearchResultView


def get_source_in(req: Request):
    source_in = req.query.get('source_in', None)
    if source_in is not None:
        source_in = source_in.split(',')
    else:
        source_in = None
    return source_in


async def render(req: Request, **kwargs):
    """/search handler

    :type app: feeluown.app.App
    """
    # pylint: disable=too-many-locals,too-many-branches
    q = req.query.get('q', '')
    if not q:
        return

    app: 'GuiApp' = req.ctx['app']
    source_in = get_source_in(req)
    search_type = SearchType(req.query.get('type', SearchType.so.value))

    view = SearchResultView(app)
    app.ui.right_panel.set_body(view)
    await view.search_and_render(q, search_type, source_in)
