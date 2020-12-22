async def render(req, **kwargs):
    app = req.ctx['app']
    model = req.ctx['model']
    app.ui.right_panel.show_model(model)
