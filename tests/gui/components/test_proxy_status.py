from feeluown.gui.components.proxy_status import ProxyStatusButton
from feeluown.i18n import t


def test_proxy_status_button_updates_sanitized_tooltip(qtbot, app_mock):
    btn = ProxyStatusButton(app_mock)
    qtbot.addWidget(btn)

    btn.update_proxies({"http": "http://user:pass@127.0.0.1:7890"})

    assert btn.toolTip() == t(
        "proxy-detected", proxy_info="http=http://127.0.0.1:7890"
    )


def test_proxy_status_button_shows_no_proxy_tooltip(qtbot, app_mock):
    btn = ProxyStatusButton(app_mock)
    qtbot.addWidget(btn)

    btn.update_proxies({})

    assert btn.toolTip() == t("proxy-not-detected")
