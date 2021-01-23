async def render(req, **kwargs):
    """/player_playlist handler
    """
    app = req.ctx['app']

    right_panel = app.ui.right_panel
    right_panel.set_body(right_panel.table_container)
    app.ui.table_container.show_player_playlist()
