from feeluown.gui.components.proxy_status import (
    ProxyStatusButton,
    sanitize_proxy_url,
    sanitize_proxies,
    format_proxies_for_display,
)
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


def test_sanitize_proxy_url_removes_userinfo():
    assert (
        sanitize_proxy_url("http://user:pass@127.0.0.1:7890")
        == "http://127.0.0.1:7890"
    )


def test_sanitize_proxies_keeps_mapping_shape():
    proxies = {
        "http": "http://user:pass@127.0.0.1:7890",
        "https": "socks5://127.0.0.1:7891",
    }

    assert sanitize_proxies(proxies) == {
        "http": "http://127.0.0.1:7890",
        "https": "socks5://127.0.0.1:7891",
    }


def test_sanitize_proxy_url_keeps_ipv6_host_brackets():
    assert (
        sanitize_proxy_url("http://user:pass@[::1]:7890")
        == "http://[::1]:7890"
    )


def test_format_proxies_for_display_uses_sanitized_values():
    proxies = {"http": "http://user:pass@127.0.0.1:7890"}

    assert format_proxies_for_display(proxies) == "http=http://127.0.0.1:7890"
