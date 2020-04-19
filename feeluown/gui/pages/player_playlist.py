async def render(req, **kwargs):
    """/player_playlist handler
    """
    app = req.ctx['app']

    app.ui.right_panel.collection_container.hide()
    app.ui.right_panel.table_container.show()
    app.ui.table_container.show_player_playlist()
